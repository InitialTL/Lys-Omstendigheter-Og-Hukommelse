const OPTIONS: string[] = ["Total darkness", "Warm light", "Super bright"];

type LightsettingProps = {
    title: string;
    onFinished: (lighting: string) => void;
};

function LightsettingQ({ title, onFinished }: LightsettingProps) {
    return (
        <div>
            <h1>{title}</h1>
            <img src="/images/lightLevels.png"
                alt="Image displaying different light levels mesured in kelvin."
                style={{ display: "block" }}
                width={"50%"}
            />
            <input type="text" placeholder="lightlevel"/>K
            <p className="notice">If you are in total darkness, write 0K</p>
            
            <button onClick={() => onFinished("LIGHT")}>
                Send inn
            </button>
        </div>
    );
}

export default LightsettingQ;