use pyo3::prelude::*;

#[pyfunction]
fn filter_commands(names: Vec<String>, query: &str) -> PyResult<Vec<usize>> {
    let query_lower = query.to_lowercase();
    if query_lower.is_empty() {
        return Ok((0..names.len()).collect());
    }

    let mut result: Vec<usize> = Vec::new();
    for (idx, name) in names.iter().enumerate() {
        if name.to_lowercase().contains(&query_lower) {
            result.push(idx);
        }
    }

    Ok(result)
}

#[pymodule]
fn _native(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_wrapped(wrap_pyfunction!(filter_commands))?;
    Ok(())
}
