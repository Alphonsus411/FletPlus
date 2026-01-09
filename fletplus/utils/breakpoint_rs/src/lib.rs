use pyo3::prelude::*;

#[pyfunction]
fn select_breakpoint(keys: Vec<i64>, value: i64) -> Option<i64> {
    if keys.is_empty() {
        return None;
    }

    let mut left = 0usize;
    let mut right = keys.len();

    while left < right {
        let mid = (left + right) / 2;
        if keys[mid] <= value {
            left = mid + 1;
        } else {
            right = mid;
        }
    }

    if left == 0 {
        None
    } else {
        Some(keys[left - 1])
    }
}

#[pymodule]
fn _native(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_wrapped(wrap_pyfunction!(select_breakpoint))?;
    Ok(())
}
