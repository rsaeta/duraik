use numpy::{ndarray::Array1, PyArray1};
use pyo3::{pyclass, pymethods, PyResult, Python};

use crate::game::actions::{Action, ActionList};

#[pyclass(name = "Action")]
struct ActionPy(Action);

#[pymethods]
impl ActionPy {
    #[getter]
    fn get_action(&self) -> PyResult<String> {
        match self.0 {
            Action::StopAttack => Ok(String::from("StopAttack")),
            Action::Take => Ok(String::from("Take")),
            Action::Attack(card) => Ok(format!("Attack({:?})", card)),
            Action::Defend(card) => Ok(format!("Defend({:?})", card)),
        }
    }

    fn to_index(&self) -> PyResult<u8> {
        Ok(u8::from(self.0))
    }
}

#[pyclass(name = "ActionList")]
pub struct ActionListPy(pub ActionList);

#[pymethods]
impl ActionListPy {
    #[getter]
    pub fn get_actions(&self) -> PyResult<Vec<String>> {
        Ok(self.0.to_strings())
    }

    pub fn to_indices(&self) -> PyResult<Vec<u8>> {
        Ok(self.0.to_u8s())
    }

    pub fn to_bitmap(&self) -> PyResult<pyo3::Py<PyArray1<bool>>> {
        let arr = Array1::from_vec(self.0.to_bitmap());
        Ok(Python::with_gil(|py| {
            PyArray1::from_array(py, &arr).to_owned()
        }))
    }
}
