mod game;
use crate::game::run_game;

fn main() {
    use rayon::prelude::*;
    let num_games = 10000;
    let range = 0..num_games;
    let results = range
        .into_par_iter()
        .map(|_| run_game())
        .reduce(|| (0., 0.), |(p1, p2), (_p1, _p2)| (p1 + _p1, p2 + _p2));
    println!("Results: {:?}", results);
}
