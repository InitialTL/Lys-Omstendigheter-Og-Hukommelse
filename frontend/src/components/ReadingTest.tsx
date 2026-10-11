import { useState } from "react";

type Text = {
    title: string;
    content: string;
    onFinished: () => void;
};

function ReadingTest({ title, content, onFinished }: Text) {
    return (
        <div>
            <h1>{title}</h1>
            <p>{content}</p>
            <button onClick={() => {
                onFinished();
            }}>
                Finished reading
            </button>
        </div>
    );
}

export default ReadingTest;