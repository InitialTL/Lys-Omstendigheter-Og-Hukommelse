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
                        <label key={optionIndex} style={{ display: "block" }}>
                            <input
                                type="radio"
                                key={optionIndex}
                                name={`question-${optionIndex}`}
                                value={option}
                            />
                            {option}
                        </label>
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