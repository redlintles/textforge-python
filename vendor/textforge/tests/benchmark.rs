#[cfg(feature = "test_access")]
#[cfg(test)]
pub mod benchmark {
    use std::time::Instant;
    use textforge::{
        api::processor::{TextForgeProcessor, TextForgeProcessorMethods},
        utils::test_helpers::build_all_tokens_pipeline_safe,
    };

    use textforge::utils::errors::TextForgeError;

    #[test]
    fn debug_overhead_too_high() -> Result<(), TextForgeError> {
        let debug_exectime_cb = || -> Result<f64, TextForgeError> {
            let runs = 100;

            let mut total = 0.0;

            let mut processor = TextForgeProcessor::new();

            let identifier = build_all_tokens_pipeline_safe(&mut processor)?;

            for _ in 0..runs {
                let start = Instant::now();

                let string_to_process = "Banana Laranja cheia de canja";

                processor.process_all_with_debug(&identifier, string_to_process)?;

                let elapsed = start.elapsed().as_secs_f64();

                total += elapsed;
            }

            let avg = total / (runs as f64);

            Ok(avg)
        };

        let no_debug_exectime_cb = || -> Result<f64, TextForgeError> {
            let runs = 100;

            let mut total = 0.0;

            let mut processor = TextForgeProcessor::new();

            let identifier = build_all_tokens_pipeline_safe(&mut processor)?;

            for _ in 0..runs {
                let start = Instant::now();

                let string_to_process = "Banana Laranja cheia de canja";

                processor.process_all(&identifier, string_to_process)?;

                let elapsed = start.elapsed().as_secs_f64();

                total += elapsed;
            }

            let avg = total / (runs as f64);
            Ok(avg)
        };

        let debug_exectime = debug_exectime_cb()?;
        let no_debug_exectime = no_debug_exectime_cb()?;

        let max_tolerance = no_debug_exectime * 100.0;

        println!(
            "Execução do método process_all_with_debug: {:.6}",
            debug_exectime
        );
        println!("Execução do método process_all: {:.6}", no_debug_exectime);
        println!("Tolerância máxima: {:.6}", max_tolerance);

        assert!(
            debug_exectime < max_tolerance,
            "Overhead do debug muito alto"
        );
        Ok(())
    }

    #[test]
    fn process_sbs_all_tokens() -> Result<(), TextForgeError> {
        let runs = 100;

        let mut total = 0.0;

        let mut processor = TextForgeProcessor::new();

        let identifier = build_all_tokens_pipeline_safe(&mut processor)?;

        for _ in 0..runs {
            let start = Instant::now();

            let string_to_process = "Banana Laranja cheia de canja";

            let processed_string =
                processor.process_all_with_debug(&identifier, string_to_process)?;

            println!("{}", processed_string);
            let elapsed = start.elapsed().as_secs_f64();

            total += elapsed;
        }

        let avg = total / (runs as f64);

        println!("Média: {:.6} Segundos", avg);

        assert!(avg < 0.03, "Executou muito devagar");
        Ok(())
    }
    #[test]
    fn process_all_tokens() -> Result<(), TextForgeError> {
        let runs = 100;

        let mut total = 0.0;

        let mut processor = TextForgeProcessor::new();

        let identifier = build_all_tokens_pipeline_safe(&mut processor)?;

        for _ in 0..runs {
            let start = Instant::now();

            let string_to_process = "Banana Laranja cheia de canja";

            processor.process_all(&identifier, string_to_process)?;

            let elapsed = start.elapsed().as_secs_f64();

            total += elapsed;
        }

        let avg = total / (runs as f64);

        println!("Média: {:.6} Segundos", avg);

        assert!(avg < 0.003, "Executou muito devagar");
        Ok(())
    }
}
