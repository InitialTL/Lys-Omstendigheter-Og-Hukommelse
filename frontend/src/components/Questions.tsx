export type Question = {
    question: string;
    options: string[];
    points: number;
};

type QuestionsProps = {
    title: string;
    questions: Question[];
    onFinished: () => void;
};

function Questions({ title, questions, onFinished }: QuestionsProps) {
    return (
        <div className="questions">
            <h1>{title}</h1>

            {questions.map((q, index) => (
                <div key={index}>
                    <h2>{q.question}</h2>

                    {q.options.map((option, optionIndex) => (
                        <p key={optionIndex}>
                            {optionIndex + 1}. {option}
                        </p>
                    ))}

                    <p>Poeng: {q.points}</p>
                </div>
            ))}

            <button onClick={() => {
                onFinished();
            }}>
                Send
            </button>
        </div>
    );
}

export default Questions;