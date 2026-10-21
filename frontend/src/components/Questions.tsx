import { useState } from "react";

export type Question = {
    question: string;
    options: string[];
    points: number;
};

type QuestionsProps = {
    title: string;
    questions: Question[];
    onFinished: (answers: number[]) => void;
};

function Questions({ title, questions, onFinished }: QuestionsProps) {
    const [answers, setAnswers] = useState<number[]>(
        Array(questions.length).fill(-1)
    );

    function selectAnswer(questionIndex: number, optionIndex: number) {
        setAnswers(prev => 
            prev.map((answer, index) => 
                index === questionIndex ? optionIndex : answer
            )
        );
    }

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
                                name={`question-${index}`}
                                value={option}
                                checked={answers[index] === optionIndex}
                                onChange={() => selectAnswer(index, optionIndex)}
                            />
                            {option}
                        </label>
                    ))}

                    <p>Poeng: {q.points}</p>
                </div>
            ))}

            <button 
                disabled={answers.includes(-1)}
                onClick={() => {
                    onFinished(answers);
                }}>
                Send
            </button>
        </div>
    );
}

export default Questions;