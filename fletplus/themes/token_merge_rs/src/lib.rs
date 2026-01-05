use pyo3::exceptions::PyTypeError;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyIterator, PyMapping};

fn mapping_to_dict(py: Python<'_>, obj: &PyAny, context: &str) -> PyResult<Py<PyDict>> {
    let mapping = PyMapping::try_from(obj).map_err(|_| {
        PyErr::new::<PyTypeError, _>(format!("{context} debe ser un mapeo"))
    })?;

    let result = PyDict::new(py);
    let items = mapping.items()?;
    for pair in PyIterator::from_object(py, items.as_ref())? {
        let (key, value): (PyObject, PyObject) = pair?.extract()?;
        result.set_item(key, value)?;
    }

    Ok(result.into())
}

fn merge_group(
    py: Python<'_>,
    target: &PyDict,
    updates: &PyDict,
) -> PyResult<()> {
    for (key, value) in updates.iter() {
        target.set_item(key, value)?;
    }
    Ok(())
}

#[pyfunction]
fn merge_token_layers(
    py: Python<'_>,
    base: &PyAny,
    layers: Vec<&PyAny>,
) -> PyResult<Py<PyDict>> {
    let base_dict = mapping_to_dict(py, base, "base")?;
    let result = PyDict::new(py);

    for (group, values) in base_dict.as_ref(py).iter() {
        let copied_values = mapping_to_dict(py, values, "base layer")?;
        result.set_item(group, copied_values.as_ref(py))?;
    }

    for (index, layer) in layers.iter().enumerate() {
        let context = format!("layer {index}");
        let layer_dict = mapping_to_dict(py, layer, &context)?;

        for (group, values) in layer_dict.as_ref(py).iter() {
            let values_context = format!("{context} values");
            let values_dict = mapping_to_dict(py, values, &values_context)?;
            let target = match result.get_item(group) {
                Some(existing) => existing
                    .downcast::<PyDict>()
                    .map_err(|_| PyErr::new::<PyTypeError, _>("Los grupos deben ser diccionarios"))?,
                None => {
                    let fresh = PyDict::new(py);
                    result.set_item(group, fresh)?;
                    fresh
                }
            };
            merge_group(py, target, values_dict.as_ref(py))?;
        }
    }

    Ok(result.into())
}

#[pymodule]
fn _native(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_wrapped(wrap_pyfunction!(merge_token_layers))?;
    Ok(())
}
