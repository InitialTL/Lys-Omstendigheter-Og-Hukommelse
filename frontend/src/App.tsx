import { useState, useEffect } from "react";
import ReadingTest from "./components/ReadingTest.tsx";
import Introduction from "./components/Introduction.tsx";
import Questions from "./components/Questions.tsx";
import LightsettingQ from "./components/LightsettingQ.tsx";
import type { Question } from "./components/Questions.tsx";

type Stage = "introduction" | "reading" | "questions" | "lighting" | "finished";

function App() {
  const [stage, setStage] = useState<Stage>("introduction");
  const [textIndex, setTextIndex] = useState<number>(0);
  const [text, setText] = useState<string>("");
  const [loadedText, setLoadedText] = useState<number | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [loadedQuestions, setLoadedQuestions] = useState<number | null>(null);
  
  function nextText() {
    if (textIndex < 2) {
      setTextIndex(prev => prev + 1);
      setStage("reading");
    } else {
      setStage("lighting");
    }
}

async function submitAnswers(answers: number[]) {
  try {
    const response = await fetch(`/api/answers/${textIndex}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ answers }),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }

    const result = await response.json();

    console.log("Score:", result.score);
    console.log("Maximum score:", result.max_score);

    nextText();
  } catch (error) {
    console.error("Failed to submit answers:", error);
  }
}

  useEffect(() => {
    async function getText() {
      const response = await fetch(`/api/text/${textIndex}`);
      const data = await response.json();

      setText(data.text);
      setLoadedText(textIndex);
    }

    getText();
  }, [textIndex]);

  useEffect(() => {
    const controller = new AbortController();

    async function getQuestions() {
      try {
        const response = await fetch(`/api/questions/${textIndex}`, { signal: controller.signal });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        setQuestions(data.questions);
        setLoadedQuestions(textIndex);
      } catch (error) {
        if (!controller.signal.aborted) {
          console.error("Failed to fetch questions", error);
        }
      }
    }

    getQuestions();
    return () => controller.abort();
  }, [textIndex]);

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
      if (loadedText !== textIndex) {
        return <p>Loading text...</p>
      }
      return (
        <ReadingTest
          title="Hello"
          content={text}
          onFinished={() => setStage("questions")}
        />
      );

    case "questions":
      if (loadedQuestions !== textIndex) {
        return <p>Loading questions...</p>
      }

      return (
        <Questions 
          key={textIndex}
          title={`Questions for text ${textIndex + 1}`}
          questions={questions}
          onFinished={submitAnswers}
        />
      );

    case "lighting":
      return (
        <LightsettingQ 
          title={"What light setting are you sitting in?"}
          onFinished={(lighting) => {
            console.log(lighting);
            setStage("finished");
          }}
        />
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