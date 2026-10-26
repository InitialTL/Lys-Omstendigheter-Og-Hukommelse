type LightingProps = {
    lighting: string;
    onFinished: () => void;
};

function Lighting({ lighting, onFinished }: LightingProps) {
    const descriptions: Record<string, string> = {
        OFF: "Turn off the room lights.",
        "3000K": "Set the lights to 3000 K (warm white).",
        "10000K": "Set the lights to 10 000 K (cool white).",
    };

    return (
        <div>
            <h1>Prepare your lighting</h1>

            <h2>{lighting === "off" ? "Lights off" : lighting}</h2>

            <p>{descriptions[lighting]}</p>

            <p>
                Make sure your lighting is correct before continuing.
            </p>

            <button onClick={onFinished}>
                Lighting is ready
            </button>
        </div>
    );
}

export default Lighting;