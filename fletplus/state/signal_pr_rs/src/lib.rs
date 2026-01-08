#![allow(non_local_definitions)]

use std::collections::HashMap;

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};

#[derive(Debug)]
struct SignalEntry {
    token: usize,
    callback: Py<PyAny>,
}

#[pyclass]
struct SignalState {
    entries: Vec<SignalEntry>,
    index: HashMap<usize, usize>,
}

#[pymethods]
impl SignalState {
    #[new]
    fn new() -> Self {
        Self {
            entries: Vec::new(),
            index: HashMap::new(),
        }
    }

    fn add(&mut self, token: usize, callback: Py<PyAny>) {
        if let Some(&pos) = self.index.get(&token) {
            if let Some(entry) = self.entries.get_mut(pos) {
                entry.callback = callback;
            }
            return;
        }
        let pos = self.entries.len();
        self.entries.push(SignalEntry { token, callback });
        self.index.insert(token, pos);
    }

    fn remove(&mut self, token: usize) {
        if let Some(pos) = self.index.remove(&token) {
            self.entries.swap_remove(pos);
            if pos < self.entries.len() {
                let moved = &self.entries[pos];
                self.index.insert(moved.token, pos);
            }
        }
    }

    fn notify(&self, py: Python<'_>, value: Py<PyAny>) -> PyResult<()> {
        let mut callbacks: Vec<Py<PyAny>> = Vec::with_capacity(self.entries.len());
        for entry in &self.entries {
            callbacks.push(entry.callback.clone_ref(py));
        }
        for callback in callbacks {
            callback.call1(py, (value.as_ref(py),))?;
        }
        Ok(())
    }

    fn snapshot(&self, py: Python<'_>) -> Py<PyList> {
        let mut callbacks = Vec::with_capacity(self.entries.len());
        for entry in &self.entries {
            callbacks.push(entry.callback.clone_ref(py).into_py(py));
        }
        PyList::new(py, callbacks).into_py(py)
    }
}

#[pyfunction]
fn notify(py: Python<'_>, subscribers: &PyAny, value: Py<PyAny>) -> PyResult<()> {
    if let Ok(state) = subscribers.extract::<PyRef<SignalState>>() {
        return state.notify(py, value);
    }
    if let Ok(dict) = subscribers.downcast::<PyDict>() {
        let mut callbacks: Vec<Py<PyAny>> = Vec::with_capacity(dict.len());
        for (_, callback) in dict.iter() {
            callbacks.push(callback.into_py(py));
        }
        for callback in callbacks {
            callback.call1(py, (value.as_ref(py),))?;
        }
        return Ok(());
    }
    Err(pyo3::exceptions::PyTypeError::new_err(
        "subscribers debe ser SignalState o dict",
    ))
}

#[pyfunction]
fn snapshot(py: Python<'_>, signals: &PyAny) -> PyResult<Py<PyDict>> {
    let dict = signals
        .downcast::<PyDict>()
        .map_err(|_| pyo3::exceptions::PyTypeError::new_err("signals debe ser dict"))?;
    let snapshot = PyDict::new(py);
    for (name, signal) in dict.iter() {
        let value = signal.call_method0("get")?;
        snapshot.set_item(name, value)?;
    }
    Ok(snapshot.into_py(py))
}

#[pymodule]
fn _native(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_class::<SignalState>()?;
    m.add_function(wrap_pyfunction!(notify, m)?)?;
    m.add_function(wrap_pyfunction!(snapshot, m)?)?;
    Ok(())
}
