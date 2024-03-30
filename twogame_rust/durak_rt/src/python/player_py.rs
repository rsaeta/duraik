use pyo3::{Py, PyAny, Python};

use crate::{
    game::{
        actions::Action,
        game::{ObservableGameState, Player},
    },
    ObservableGameStatePy,
};

pub struct PyPlayer(pub Py<PyAny>);

impl Player for PyPlayer {
    fn choose_action(
        &mut self,
        state: ObservableGameState,
        actions: Vec<Action>,
        history: Vec<ObservableGameState>,
    ) -> Action {
        let state_py = ObservableGameStatePy::from(state);
        let actions_py: Vec<String> = actions.iter().map(|a| format!("{:?}", a)).collect();
        let history_py: Vec<ObservableGameStatePy> = history
            .iter()
            .map(|x| ObservableGameStatePy::from(x))
            .collect();

        let res = Python::with_gil(|py| {
            let action = (*self)
                .0
                .call_method(
                    py,
                    "choose_action",
                    (state_py, actions_py, history_py),
                    None,
                )
                .unwrap();
            action.extract::<u8>(py).unwrap()
        });
        actions[res as usize]
    }
}
