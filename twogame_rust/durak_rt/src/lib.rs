use pyo3::prelude::*;

#[pyfunction]
fn add(a: usize, b: usize) -> PyResult<String> {
    Ok((a + b).to_string())
}

#[pyfunction]
fn docrazyshit() -> PyResult<String> {
    Ok("I'm doing crazy shit updated".to_string())
}

#[pymodule]
#[pyo3(name = "rust")]
fn rust(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(add, m)?)?;
    m.add_function(wrap_pyfunction!(docrazyshit, m)?)?;
    Ok(())
}
