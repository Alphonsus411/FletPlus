use std::collections::{HashMap, HashSet};

use pyo3::prelude::*;
use pyo3::types::{PyAny, PyIterator};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
struct ListenerKey {
    owner_id: Option<usize>,
    func_id: usize,
}

impl ListenerKey {
    fn from_callback(callback: &PyAny) -> PyResult<Self> {
        if let (Ok(owner), Ok(func)) = (
            callback.getattr("__self__"),
            callback.getattr("__func__"),
        ) {
            if !owner.is_none() {
                return Ok(Self {
                    owner_id: Some(owner.as_ptr() as usize),
                    func_id: func.as_ptr() as usize,
                });
            }
        }

        Ok(Self {
            owner_id: None,
            func_id: callback.as_ptr() as usize,
        })
    }
}

#[derive(Debug)]
struct ListenerEntry {
    weak: Py<PyAny>,
    key: ListenerKey,
}

impl ListenerEntry {
    fn upgrade(&self, py: Python<'_>) -> Option<Py<PyAny>> {
        match self.weak.call0(py) {
            Ok(obj) if !obj.is_none(py) => Some(obj.into_py(py)),
            _ => None,
        }
    }
}

#[pyclass]
struct ListenerContainer {
    listeners: HashMap<String, Vec<ListenerEntry>>,
    fired: HashSet<String>,
    weak_ref: Py<PyAny>,
    weak_method: Py<PyAny>,
}

#[pymethods]
impl ListenerContainer {
    #[new]
    fn new(py: Python<'_>) -> PyResult<Self> {
        let weakref_mod = py.import("weakref")?;
        let weak_ref = weakref_mod.getattr("ref")?.into_py(py);
        let weak_method = weakref_mod.getattr("WeakMethod")?.into_py(py);
        Ok(Self {
            listeners: HashMap::new(),
            fired: HashSet::new(),
            weak_ref,
            weak_method,
        })
    }

    fn reset(&mut self) {
        self.listeners.clear();
        self.fired.clear();
    }

    fn add_listener(
        mut slf: PyRefMut<'_, Self>,
        py: Python<'_>,
        trigger: &str,
        callback: Py<PyAny>,
        replay_if_fired: bool,
    ) -> PyResult<Py<Unsubscriber>> {
        let entry = slf.build_entry(py, callback)?;
        let key = entry.key;
        let was_fired = slf.fired.contains(trigger);
        let storage = slf.listeners.entry(trigger.to_string()).or_default();
        storage.push(entry);

        if replay_if_fired && was_fired {
            if let Some(cb) = storage
                .last()
                .and_then(|last| last.upgrade(py))
            {
                let _ = cb.call1(py, (trigger,));
            }
        }

        let container: Py<ListenerContainer> = slf.into();
        let unsub = Py::new(
            py,
            Unsubscriber {
                container,
                trigger: trigger.to_string(),
                key,
            },
        )?;
        Ok(unsub)
    }

    fn remove_listener(
        &mut self,
        py: Python<'_>,
        trigger: &str,
        callback: Py<PyAny>,
    ) -> PyResult<()> {
        let key = ListenerKey::from_callback(callback.as_ref(py))?;
        self.remove_by_key(py, trigger, &key);
        Ok(())
    }

    fn trigger(&mut self, py: Python<'_>, name: &str) {
        if let Some(items) = self.listeners.get_mut(name) {
            let mut retained = Vec::with_capacity(items.len());
            for entry in std::mem::take(items) {
                if let Some(callback) = entry.upgrade(py) {
                    if callback.call1(py, (name,)).is_ok() {
                        retained.push(entry);
                    }
                }
            }
            if retained.is_empty() {
                self.listeners.remove(name);
            } else {
                *items = retained;
            }
        }
        self.fired.insert(name.to_string());
    }

    fn trigger_many(&mut self, py: Python<'_>, names: &PyAny) -> PyResult<()> {
        let iterable = PyIterator::from_object(names)?;
        for name in iterable {
            let value: String = name?.extract()?;
            self.trigger(py, &value);
        }
        Ok(())
    }

    fn has_fired(&self, name: &str) -> bool {
        self.fired.contains(name)
    }

    fn fired(&self) -> Vec<String> {
        self.fired.iter().cloned().collect()
    }
}

impl ListenerContainer {
    fn build_entry(&self, py: Python<'_>, callback: Py<PyAny>) -> PyResult<ListenerEntry> {
        let key = ListenerKey::from_callback(callback.as_ref(py))?;
        let target = if callback.as_ref(py).hasattr("__self__")? && callback.as_ref(py).hasattr("__func__")? {
            self.weak_method.as_ref(py)
        } else {
            self.weak_ref.as_ref(py)
        };
        let weak = target.call1((callback.as_ref(py),))?.into_py(py);
        Ok(ListenerEntry { weak, key })
    }

    fn remove_by_key(&mut self, py: Python<'_>, trigger: &str, key: &ListenerKey) {
        if let Some(items) = self.listeners.get_mut(trigger) {
            let mut retained = Vec::with_capacity(items.len());
            for entry in std::mem::take(items) {
                if &entry.key != key {
                    if entry.upgrade(py).is_some() {
                        retained.push(entry);
                    }
                }
            }
            if retained.is_empty() {
                self.listeners.remove(trigger);
            } else {
                *items = retained;
            }
        }
    }
}

#[pyclass]
struct Unsubscriber {
    container: Py<ListenerContainer>,
    trigger: String,
    key: ListenerKey,
}

#[pymethods]
impl Unsubscriber {
    fn __call__(&self, py: Python<'_>) -> PyResult<()> {
        let mut container = self.container.borrow_mut(py);
        container.remove_by_key(py, &self.trigger, &self.key);
        Ok(())
    }
}

#[pymodule]
fn listeners_rs(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_class::<ListenerContainer>()?;
    m.add_class::<Unsubscriber>()?;
    Ok(())
}
