use pyo3::prelude::*;
use pyo3::types::PyDict;

#[pyfunction]
fn apply_styles(
    py: Python<'_>,
    styles: Vec<(Py<PyAny>, Py<PyAny>)>,
    attrs: Vec<String>,
) -> PyResult<Vec<(Py<PyAny>, String, Py<PyAny>)>> {
    let mut updates: Vec<(Py<PyAny>, String, Py<PyAny>)> = Vec::new();

    for (control, rstyle) in styles {
        let control_ref = control.as_ref(py);
        let base_attrs = control_ref.getattr("__fletplus_base_attrs__").ok();

        if let Some(base) = base_attrs {
            if let Ok(base_dict) = base.downcast::<PyDict>() {
                for attr in &attrs {
                    if base_dict.contains(attr)? {
                        let value = base_dict.get_item(attr).unwrap_or_else(|| py.None());
                        updates.push((control.clone_ref(py), attr.clone(), value.into_py(py)));
                    }
                }
            }
        }

        let page = rstyle
            .as_ref(py)
            .getattr("_fletplus_page")
            .ok()
            .or_else(|| control_ref.getattr("page").ok());

        let page = match page {
            Some(page) if !page.is_none() => page,
            _ => continue,
        };

        let style = rstyle.as_ref(py).call_method1("get_style", (page,))?;
        if style.is_none() {
            continue;
        }

        let styled_container = style.call_method1("apply", (control_ref,))?;

        for attr in &attrs {
            if control_ref.hasattr(attr)? {
                let value = styled_container.getattr(attr)?;
                if !value.is_none() {
                    updates.push((control.clone_ref(py), attr.clone(), value.into_py(py)));
                }
            }
        }
    }

    Ok(updates)
}

#[pymodule]
fn _native(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_wrapped(wrap_pyfunction!(apply_styles))?;
    Ok(())
}
