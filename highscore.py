class HighScoreTable:
    def __init__(self, filename: str) -> None:
        self.filename = filename+".hs"

    def write_entry(self, player_name: str, score: int) -> None:
        "Write a new wntry (name/score pair) at the end of the file"
        with open(self.filename, mode='a') as file:
            file.write(f"{player_name} {score}\n")

    def print_table(self) -> None:
        with open(self.filename, mode='r') as file:
            for line in file:
                print(line.strip())

    def top_scores(self, top: int = 3):
        """Returns a list (best 3 by default)
        of tuples of top player/score pairs"""
        with open(self.filename, mode='r') as file:
            scores = [tuple(line.strip().split()) for line in file]
            scores.sort(reverse=True, key=lambda x: int(x[1]))
            for score in scores[:top]:
                yield f"{score[0]}\t{score[1]}"

