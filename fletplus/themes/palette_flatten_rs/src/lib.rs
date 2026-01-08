use pyo3::prelude::*;
use pyo3::types::PyDict;

fn flatten_mapping(py: Python<'_>, prefix: &str, value: &PyAny, out: &PyDict) -> PyResult<()> {
    if let Ok(mapping) = value.downcast::<PyDict>() {
        for (key, sub_value) in mapping.iter() {
            let key_str = key.str()?.to_str()?;
            let new_prefix = if prefix.is_empty() {
                key_str.to_string()
            } else {
                format!("{}_{}", prefix, key_str)
            };
            flatten_mapping(py, &new_prefix, sub_value, out)?;
        }
        Ok(())
    } else {
        out.set_item(prefix, value)?;
        Ok(())
    }
}

#[pyfunction]
fn flatten_palette(py: Python<'_>, palette: &PyAny) -> PyResult<Py<PyDict>> {
    let output = PyDict::new(py);
    flatten_mapping(py, "", palette, output)?;
    Ok(output.into_py(py))
}

#[pymodule]
fn _native(py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(flatten_palette, m)?)?;
    Ok(())
}
