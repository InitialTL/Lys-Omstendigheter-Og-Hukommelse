type Text = {
    title: string;
    content: string;
    onFinished: () => void;
};

function ReadingTest({ content, onFinished }: Text) {
    const [heading, ...paragraphs] = content.split(/\r?\n/);

    return (
        <div className="text">
            <h1>{heading}</h1>
            {paragraphs.map((paragraph, index) => <p key={index}>{paragraph}</p>)}
            <button onClick={() => {
                onFinished();
            }}>
                Finished reading
            </button>
        </div>
    );
}

export default ReadingTest;