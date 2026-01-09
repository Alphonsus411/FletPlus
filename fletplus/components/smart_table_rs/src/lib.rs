use pyo3::basic::CompareOp;
use pyo3::prelude::*;
use pyo3::types::{PyAny, PyDict, PyTuple};
use std::cmp::Ordering;

#[derive(Clone)]
struct Record {
    row_id: i64,
    values: Py<PyDict>,
}

#[derive(Clone, Copy, Debug)]
enum FilterOp {
    Eq,
    Neq,
    Lt,
    Lte,
    Gt,
    Gte,
    ContainsCi,
}

impl<'source> FromPyObject<'source> for FilterOp {
    fn extract(obj: &'source PyAny) -> PyResult<Self> {
        let value: String = obj.extract()?;
        match value.as_str() {
            "eq" => Ok(FilterOp::Eq),
            "neq" => Ok(FilterOp::Neq),
            "lt" => Ok(FilterOp::Lt),
            "lte" => Ok(FilterOp::Lte),
            "gt" => Ok(FilterOp::Gt),
            "gte" => Ok(FilterOp::Gte),
            "contains_ci" => Ok(FilterOp::ContainsCi),
            _ => Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                format!("Operación de filtro no soportada: {value}"),
            )),
        }
    }
}

#[derive(FromPyObject, Clone)]
struct FilterSpec {
    key: String,
    value: PyObject,
    op: FilterOp,
}

#[derive(FromPyObject, Clone)]
struct SortSpec {
    key: String,
    ascending: bool,
}

#[derive(Debug, PartialEq)]
enum ComparableValue {
    NoneValue,
    Bool(bool),
    Int(i64),
    Float(f64),
    String(String),
}

impl ComparableValue {
    fn from_py(py: Python<'_>, any: &PyAny) -> Self {
        if any.is_none() {
            return ComparableValue::NoneValue;
        }

        if let Ok(value) = any.extract::<bool>() {
            return ComparableValue::Bool(value);
        }

        if let Ok(value) = any.extract::<i64>() {
            return ComparableValue::Int(value);
        }

        if let Ok(value) = any.extract::<f64>() {
            return ComparableValue::Float(value);
        }

        if let Ok(text) = any.str() {
            if let Ok(s) = text.to_str() {
                return ComparableValue::String(s.to_string());
            }
        }

        ComparableValue::String(format!("{:?}", any))
    }
}

fn normalize_str(py: Python<'_>, value: &PyAny) -> Option<String> {
    if value.is_none() {
        return None;
    }

    if let Ok(text) = value.str() {
        if let Ok(s) = text.to_str() {
            return Some(s.to_lowercase());
        }
    }

    None
}

fn is_empty_filter_value(value: &PyAny) -> bool {
    if value.is_none() {
        return true;
    }

    if let Ok(text) = value.str() {
        if let Ok(s) = text.to_str() {
            return s.is_empty();
        }
    }

    false
}

fn eq_values(left: &ComparableValue, right: &ComparableValue) -> bool {
    match (left, right) {
        (ComparableValue::NoneValue, ComparableValue::NoneValue) => true,
        (ComparableValue::Bool(l), ComparableValue::Bool(r)) => l == r,
        (ComparableValue::Int(l), ComparableValue::Int(r)) => l == r,
        (ComparableValue::Float(l), ComparableValue::Float(r)) => l == r,
        (ComparableValue::Bool(l), ComparableValue::Int(r)) => (*l as i64) == *r,
        (ComparableValue::Bool(l), ComparableValue::Float(r)) => (*l as i64 as f64) == *r,
        (ComparableValue::Int(l), ComparableValue::Bool(r)) => *l == (*r as i64),
        (ComparableValue::Float(l), ComparableValue::Bool(r)) => *l == (*r as i64 as f64),
        (ComparableValue::Int(l), ComparableValue::Float(r)) => (*l as f64) == *r,
        (ComparableValue::Float(l), ComparableValue::Int(r)) => *l == (*r as f64),
        (ComparableValue::String(l), ComparableValue::String(r)) => l == r,
        _ => false,
    }
}

fn order_values(left: &ComparableValue, right: &ComparableValue) -> Option<Ordering> {
    match (left, right) {
        (ComparableValue::Bool(l), ComparableValue::Bool(r)) => Some(l.cmp(r)),
        (ComparableValue::Int(l), ComparableValue::Int(r)) => Some(l.cmp(r)),
        (ComparableValue::Float(l), ComparableValue::Float(r)) => l.partial_cmp(r),
        (ComparableValue::Bool(l), ComparableValue::Int(r)) => (*l as i64).partial_cmp(r),
        (ComparableValue::Bool(l), ComparableValue::Float(r)) => (*l as i64 as f64).partial_cmp(r),
        (ComparableValue::Int(l), ComparableValue::Bool(r)) => l.partial_cmp(&(*r as i64)),
        (ComparableValue::Float(l), ComparableValue::Bool(r)) => l.partial_cmp(&(*r as i64 as f64)),
        (ComparableValue::Int(l), ComparableValue::Float(r)) => (*l as f64).partial_cmp(r),
        (ComparableValue::Float(l), ComparableValue::Int(r)) => l.partial_cmp(&(*r as f64)),
        (ComparableValue::String(l), ComparableValue::String(r)) => Some(l.cmp(r)),
        _ => None,
    }
}

fn matches_filter(py: Python<'_>, record: &Record, filter: &FilterSpec) -> PyResult<bool> {
    let filter_value = filter.value.as_ref(py);
    if is_empty_filter_value(filter_value) {
        return Ok(true);
    }

    let dict = record.values.as_ref(py);
    match filter.op {
        FilterOp::ContainsCi => {
            let Some(cell_value) = dict.get_item(&filter.key) else {
                return Ok(false);
            };

            let Some(normalized_filter) = normalize_str(py, filter_value) else {
                return Ok(true);
            };

            if normalized_filter.is_empty() {
                return Ok(true);
            }

            let Some(normalized_cell) = normalize_str(py, cell_value) else {
                return Ok(false);
            };

            Ok(normalized_cell.contains(&normalized_filter))
        }
        FilterOp::Eq | FilterOp::Neq | FilterOp::Lt | FilterOp::Lte | FilterOp::Gt | FilterOp::Gte => {
            let cell_value = dict
                .get_item(&filter.key)
                .map(|value| ComparableValue::from_py(py, value))
                .unwrap_or(ComparableValue::NoneValue);
            let filter_value = ComparableValue::from_py(py, filter_value);

            match filter.op {
                FilterOp::Eq => Ok(eq_values(&cell_value, &filter_value)),
                FilterOp::Neq => Ok(!eq_values(&cell_value, &filter_value)),
                FilterOp::Lt => Ok(order_values(&cell_value, &filter_value) == Some(Ordering::Less)),
                FilterOp::Lte => Ok(matches!(
                    order_values(&cell_value, &filter_value),
                    Some(Ordering::Less | Ordering::Equal)
                )),
                FilterOp::Gt => Ok(order_values(&cell_value, &filter_value) == Some(Ordering::Greater)),
                FilterOp::Gte => Ok(matches!(
                    order_values(&cell_value, &filter_value),
                    Some(Ordering::Greater | Ordering::Equal)
                )),
                FilterOp::ContainsCi => Ok(false),
            }
        }
    }
}

fn fallback_str(value: &PyAny) -> String {
    value
        .str()
        .and_then(|text| text.to_str())
        .map(|text| text.to_string())
        .unwrap_or_else(|_| format!("{:?}", value))
}

fn compare_python_values(py: Python<'_>, left: &PyAny, right: &PyAny) -> PyResult<Ordering> {
    if left
        .rich_compare(right, CompareOp::Lt)?
        .is_true()?
    {
        return Ok(Ordering::Less);
    }

    if left
        .rich_compare(right, CompareOp::Gt)?
        .is_true()?
    {
        return Ok(Ordering::Greater);
    }

    Ok(Ordering::Equal)
}

fn compare_sort_values(
    py: Python<'_>,
    left: Option<&PyAny>,
    right: Option<&PyAny>,
) -> Ordering {
    let left_is_none = left.map_or(true, |value| value.is_none());
    let right_is_none = right.map_or(true, |value| value.is_none());

    match (left_is_none, right_is_none) {
        (true, true) => Ordering::Equal,
        (true, false) => Ordering::Greater,
        (false, true) => Ordering::Less,
        (false, false) => {
            let Some(left_value) = left else {
                return Ordering::Equal;
            };
            let Some(right_value) = right else {
                return Ordering::Equal;
            };

            if let Ok(ordering) = compare_python_values(py, left_value, right_value) {
                return ordering;
            }

            fallback_str(left_value).cmp(&fallback_str(right_value))
        }
    }
}

fn compare_records(
    py: Python<'_>,
    left: &Record,
    right: &Record,
    sort: &SortSpec,
) -> PyResult<Ordering> {
    let left_value = left.values.as_ref(py).get_item(&sort.key);
    let right_value = right.values.as_ref(py).get_item(&sort.key);

    let ordering = compare_sort_values(py, left_value, right_value);

    Ok(if sort.ascending {
        ordering
    } else {
        ordering.reverse()
    })
}

fn parse_records(py: Python<'_>, items: Vec<PyObject>) -> PyResult<Vec<Record>> {
    let mut records: Vec<Record> = Vec::with_capacity(items.len());

    for item in items {
        let tuple: &PyTuple = item.as_ref(py).downcast()?;
        if tuple.len() != 2 {
            return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                "Cada registro debe ser (row_id, dict)",
            ));
        }

        let row_id: i64 = tuple.get_item(0)?.extract()?;
        let values: &PyDict = tuple.get_item(1)?.downcast()?;

        records.push(Record {
            row_id,
            values: values.into(),
        });
    }

    Ok(records)
}

#[pyfunction]
/// Aplica filtros y ordenamientos sobre los registros.
///
/// Contrato de filtros:
/// - `filters` es una lista de dicts con claves `key`, `value` y `op`.
/// - `op` soporta: `contains_ci`, `eq`, `neq`, `lt`, `lte`, `gt`, `gte`.
/// - `contains_ci` convierte ambos valores a string y compara por inclusión sin
///   distinguir mayúsculas/minúsculas.
/// - Los operadores de comparación usan el valor original del registro y del
///   filtro. Si no son comparables, el filtro no aplica.
fn apply_query_inner(
    py: Python<'_>,
    records: Vec<PyObject>,
    filters: Vec<FilterSpec>,
    sorts: Vec<SortSpec>,
) -> PyResult<Vec<i64>> {
    let parsed_records = parse_records(py, records)?;

    let mut filtered: Vec<Record> = Vec::with_capacity(parsed_records.len());
    for record in parsed_records.into_iter() {
        let mut keep = true;
        for filter in &filters {
            if !matches_filter(py, &record, filter)? {
                keep = false;
                break;
            }
        }
        if keep {
            filtered.push(record);
        }
    }

    let mut sorted = filtered;

    for sort in sorts.iter().rev() {
        sorted.sort_by(|left, right| compare_records(py, left, right, sort).unwrap_or(Ordering::Equal));
    }

    Ok(sorted.into_iter().map(|record| record.row_id).collect())
}

#[pyfunction]
/// Aplica filtros y ordenamientos sobre los registros.
///
/// Contrato de filtros:
/// - `filters` es una lista de dicts con claves `key`, `value` y `op`.
/// - `op` soporta: `contains_ci`, `eq`, `neq`, `lt`, `lte`, `gt`, `gte`.
/// - `contains_ci` convierte ambos valores a string y compara por inclusión sin
///   distinguir mayúsculas/minúsculas.
/// - Los operadores de comparación usan el valor original del registro y del
///   filtro. Si no son comparables, el filtro no aplica.
fn apply_query(
    py: Python<'_>,
    records: Vec<PyObject>,
    filters: Vec<FilterSpec>,
    sorts: Vec<SortSpec>,
) -> PyResult<Vec<i64>> {
    apply_query_inner(py, records, filters, sorts)
}

#[pyfunction]
/// Devuelve los IDs ordenados finales para filtros/ordenamiento compatibles.
fn apply_query_ids(
    py: Python<'_>,
    records: Vec<PyObject>,
    filters: Vec<FilterSpec>,
    sorts: Vec<SortSpec>,
) -> PyResult<Vec<i64>> {
    apply_query_inner(py, records, filters, sorts)
}

#[pymodule]
fn _native(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(apply_query, m)?)?;
    m.add_function(wrap_pyfunction!(apply_query_ids, m)?)?;
    Ok(())
}
