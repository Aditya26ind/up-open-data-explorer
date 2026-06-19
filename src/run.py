import .analyse
import .collect_data
import .consolidate_data
import .utils

class Pipeline:
    def __init__(self, steps):
        self.steps = steps

    def run(self, data):
        # Run each step in sequence, passing the output of one as input to the next
        for step in self.steps:
            data = step.run(data)
        return data
    
if __name__ == "__main__":
    # Define the steps of the pipeline
    steps = [
        collect_data.Extraction(),
        consolidate_data.Transformation("Flatten and Clean", consolidate_data._flatten_row),
        analyse.Analysis(),
    ]

    # Create and run the pipeline
    pipeline = Pipeline(steps)
    pipeline.run(None)  # Initial input is None since Extraction doesn't require input