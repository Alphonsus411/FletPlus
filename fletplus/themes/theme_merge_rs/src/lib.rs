use pyo3::exceptions::PyTypeError;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyIterator, PyMapping, PyString};

fn mapping_to_dict(py: Python<'_>, obj: &PyAny) -> PyResult<Py<PyDict>> {
    let mapping = PyMapping::try_from(obj)?;
    let result = PyDict::new(py);
    let items = mapping.items()?;
    for pair in PyIterator::from_object(py, items.as_ref())? {
        let (key, value): (PyObject, PyObject) = pair?.extract()?;
        result.set_item(key, value)?;
    }
    Ok(result.into())
}

fn merge_groups(py: Python<'_>, target: &PyDict, updates: &PyAny) -> PyResult<()> {
    let mapping = match PyMapping::try_from(updates) {
        Ok(mapping) => mapping,
        Err(_) => return Ok(()),
    };

    let items = mapping.items()?;
    for pair in PyIterator::from_object(py, items.as_ref())? {
        let (group, values): (PyObject, PyObject) = pair?.extract()?;
        let values_any = values.as_ref(py);
        let values_mapping = match PyMapping::try_from(values_any) {
            Ok(values_mapping) => values_mapping,
            Err(_) => continue,
        };

        let existing = target.get_item(group.clone());
        let next_target = match existing {
            Some(existing) => match existing.downcast::<PyDict>() {
                Ok(existing_dict) => existing_dict,
                Err(_) => {
                    let copied = mapping_to_dict(py, values_mapping.as_ref())?;
                    target.set_item(group, copied.as_ref(py))?;
                    continue;
                }
            },
            None => {
                let copied = mapping_to_dict(py, values_mapping.as_ref())?;
                target.set_item(group.clone(), copied.as_ref(py))?;
                continue;
            }
        };

        let values_dict = mapping_to_dict(py, values_mapping.as_ref())?;
        for (key, value) in values_dict.as_ref(py).iter() {
            next_target.set_item(key, value)?;
        }
    }

    Ok(())
}

#[pyfunction]
fn merge_token_groups(py: Python<'_>, base: &PyAny, updates: &PyAny) -> PyResult<Py<PyDict>> {
    let base_dict = base.downcast::<PyDict>().map_err(|_| {
        PyErr::new::<PyTypeError, _>("base debe ser un diccionario")
    })?;

    merge_groups(py, base_dict, updates)?;
    Ok(base_dict.into())
}

#[pyfunction]
fn merge_variant_overrides(
    py: Python<'_>,
    definition: &PyAny,
    common_tokens: &PyAny,
    overrides: &PyAny,
) -> PyResult<Py<PyDict>> {
    let definition_dict = definition.downcast::<PyDict>().map_err(|_| {
        PyErr::new::<PyTypeError, _>("definition debe ser un diccionario")
    })?;

    let overrides_mapping = PyMapping::try_from(overrides).ok();
    let variants = ["light", "dark"];

    for variant in variants {
        let variant_key = PyString::new(py, variant);
        let existing = definition_dict.get_item(variant_key);
        let variant_dict = match existing {
            Some(existing) => match existing.downcast::<PyDict>() {
                Ok(existing_dict) => existing_dict,
                Err(_) => {
                    let fresh = PyDict::new(py);
                    definition_dict.set_item(variant_key, fresh)?;
                    fresh
                }
            },
            None => {
                let fresh = PyDict::new(py);
                definition_dict.set_item(variant_key, fresh)?;
                fresh
            }
        };

        merge_groups(py, variant_dict, common_tokens)?;

        if let Some(overrides_mapping) = overrides_mapping.as_ref() {
            if let Ok(Some(variant_override)) = overrides_mapping.get_item(variant_key) {
                merge_groups(py, variant_dict, variant_override.as_ref(py))?;
            }
        }
    }

    Ok(definition_dict.into())
}

#[pymodule]
fn _native(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_wrapped(wrap_pyfunction!(merge_token_groups))?;
    m.add_wrapped(wrap_pyfunction!(merge_variant_overrides))?;
    Ok(())
}
