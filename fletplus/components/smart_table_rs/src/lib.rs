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
    ContainsCi,
}

impl<'source> FromPyObject<'source> for FilterOp {
    fn extract(obj: &'source PyAny) -> PyResult<Self> {
        let value: String = obj.extract()?;
        match value.as_str() {
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

fn cmp_values(a: &ComparableValue, b: &ComparableValue) -> Ordering {
    match (a, b) {
        (ComparableValue::NoneValue, ComparableValue::NoneValue) => Ordering::Equal,
        (ComparableValue::NoneValue, _) => Ordering::Greater,
        (_, ComparableValue::NoneValue) => Ordering::Less,
        (ComparableValue::Bool(left), ComparableValue::Bool(right)) => left.cmp(right),
        (ComparableValue::Int(left), ComparableValue::Int(right)) => left.cmp(right),
        (ComparableValue::Float(left), ComparableValue::Float(right)) => left
            .partial_cmp(right)
            .unwrap_or(Ordering::Equal),
        (ComparableValue::String(left), ComparableValue::String(right)) => left.cmp(right),
        _ => format!("{:?}", a).cmp(&format!("{:?}", b)),
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

fn matches_filter(py: Python<'_>, record: &Record, filter: &FilterSpec) -> PyResult<bool> {
    let filter_value = normalize_str(py, filter.value.as_ref(py));
    let Some(ref normalized_filter) = filter_value else {
        return Ok(true);
    };

    if normalized_filter.is_empty() {
        return Ok(true);
    }

    let dict = record.values.as_ref(py);
    let Some(cell_value) = dict.get_item(&filter.key) else {
        return Ok(false);
    };

    let Some(normalized_cell) = normalize_str(py, cell_value) else {
        return Ok(false);
    };

    match filter.op {
        FilterOp::ContainsCi => Ok(normalized_cell.contains(normalized_filter)),
    }
}

fn compare_records(
    py: Python<'_>,
    left: &Record,
    right: &Record,
    sort: &SortSpec,
) -> PyResult<Ordering> {
    let left_value = left
        .values
        .as_ref(py)
        .get_item(&sort.key)
        .map(|value| ComparableValue::from_py(py, value))
        .unwrap_or(ComparableValue::NoneValue);

    let right_value = right
        .values
        .as_ref(py)
        .get_item(&sort.key)
        .map(|value| ComparableValue::from_py(py, value))
        .unwrap_or(ComparableValue::NoneValue);

    let ordering = cmp_values(&left_value, &right_value);

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
fn apply_query(
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

#[pymodule]
fn _native(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(apply_query, m)?)?;
    Ok(())
}
