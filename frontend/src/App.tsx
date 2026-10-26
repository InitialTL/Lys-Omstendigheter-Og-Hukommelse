import { useState, useEffect } from "react";
import ReadingTest from "./components/ReadingTest.tsx";
import Introduction from "./components/Introduction.tsx";
import Questions from "./components/Questions.tsx";
import Lighting from "./components/Lighting.tsx";
import type { Question } from "./components/Questions.tsx";

type Stage = "introduction" | "lighting" | "reading" | "questions" | "finished";

type NextText = {
  group: string;
  finished: boolean;
  text_id: number | null;
  lighting: string | null;
}

function App() {
  const [stage, setStage] = useState<Stage>("introduction");

  const [textIndex, setTextIndex] = useState<number>(0);
  const [text, setText] = useState<string>("");
  const [loadedText, setLoadedText] = useState<number | null>(null);

  const [questions, setQuestions] = useState<Question[]>([]);
  const [loadedQuestions, setLoadedQuestions] = useState<number | null>(null);

  const [participantID, setParticipantID] = useState<string | null>(() => 
    localStorage.getItem("participantID")
  );
  function saveParticipantID(id: string) {
    localStorage.setItem("participantID", id);
    setParticipantID(id);
  }
  const [lighting, setLighting] = useState<string>("");

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadNextTest(id: string) {
    const response = await fetch(`/api/participants/${id}/next`);

    if (!response.ok) {
      throw new Error(`Failed to load next test: ${response.status}`);
    }
    
    const data: NextText = await response.json();

    if (data.finished) {
      setStage("finished");
      return;
    }

    if (data.text_id === null || data.lighting === null) {
      throw new Error("Invalid test configuration");
    }

    setTextIndex(data.text_id);
    setLighting(data.lighting);
    setStage("lighting");
  }

  async function startExperiment() {
    if (busy) return;

    setBusy(true);
    setError(null);

    try {
      const existingID = localStorage.getItem("participantID");
      if (existingID) {
        setParticipantID(existingID);
        await loadNextTest(existingID);
        return;
      }

      const response = await fetch("/api/participants", {
        method: "POST",
      });

      if (!response.ok) {
        throw new Error(`Registration fialed: ${response.status}`);
      }

      const data = await response.json();

      if (data.participant_id == null) {
        throw new Error("Missing participant ID");
      }

      const id = String(data.participant_id);
      saveParticipantID(id);
      await loadNextTest(id);
    } catch(err) {
      console.error(err);
      setError("Unable to start the experiment");
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    const savedID = localStorage.getItem("participantID");

    if (!savedID) return;

    loadNextTest(savedID).catch(err => {
      console.error(err);
      setError("Unable to restore your experiment.");
    });
  }, []);

async function submitAnswers(answers: number[]) {
  if (!participantID || busy) return;

  setBusy(true);
  setError(null);

  try {
    const response = await fetch(`/api/answers/${textIndex}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        participant_id: participantID,
        answers
      }),
    });

    if (!response.ok) {
      throw new Error(`Submission failed ${response.status}`);
    }

    const result = await response.json();

    console.log("Score:", result.score);
    console.log("Maximum score:", result.max_score);

    await loadNextTest(participantID);
  } catch (err) {
    console.error(err);
    setError("Unable to submit answers. Please try again.");
  } finally {
    setBusy(false);
  }
}
  useEffect(() => {
    const controller = new AbortController();

    async function getText() {
      try {
        const response = await fetch(`/api/text/${textIndex}`, {
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        setText(data.text);
        setLoadedText(textIndex);
      } catch (err) {
      if (!controller.signal.aborted) {
        console.error("Failed to fetch text", err);
        setError("Unable to load the text.");
      }
    }
  }
  getText();
  return () => controller.abort();
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
      <>
        <Introduction
          title="Introduction"
          content="blablabla 30 minutes bla bla bla"
          onFinished={startExperiment}
        />

        {busy && <p>Registering participant...</p>}
        {error && <p>{error}</p>}
      </>
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
        <>
        <Questions 
          key={textIndex}
          title={`Questions for text ${textIndex + 1}`}
          questions={questions}
          onFinished={submitAnswers}
        />

        {busy && <p>Saving answers...</p>}
        {error && <p role="alert">{error}</p>}
        </>
      );

    case "lighting":
      return (
        <Lighting 
          lighting={lighting}
          onFinished={() => setStage("reading")}
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