type IntroductionProps = {
    title: string;
    content: string;
    onFinished: () => void;
};

function Introduction({ title, content, onFinished }: IntroductionProps) {
    return (
        <div>
            <h1>{title}</h1>
            <p>{content}</p>
            <button onClick={onFinished}>
                Start Experiment
            </button>
        </div>
    );
}

export default Introduction;