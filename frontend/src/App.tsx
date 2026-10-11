import { useState } from "react";
import ReadingTest from "./components/ReadingTest.tsx";
import Introduction from "./components/Introduction.tsx";

type Stage = "introduction" | "reading" | "questions" | "finished";

function App() {
  const [stage, setStage] = useState<Stage>("introduction");
  const [textIndex, setTextIndex] = useState<number>(0);
  
  switch (stage) {
    case "introduction":
      return (
      <Introduction
        title="Introduction"
        content="blablabla 30 minutes bla bla bla"
        onFinished={() => setStage("reading")}
      />
    );

    case "reading":
      return (
        <ReadingTest
          title="Hello"
          content="World..."
          onFinished={() => setStage("questions")}
        />
      );

    case "questions":
      return (
        <p>question bla bla bla</p>
      );
    
    case "finished":
      return (
        <p>Successfully finished!</p>
      );
    
    default:
      return (
        <p>An error occured</p>
      );
  }

}

export default App;