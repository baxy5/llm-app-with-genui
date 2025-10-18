import { PromptInputMessage } from "@/components/ai-elements/prompt-input";
import { FileUIPart } from "ai";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export async function createFileInterfaces(files: FileUIPart[]) {
  const filePromises = files.map(async (f) => {
    if (f.url) {
      try {
        const fileBlob = await fetch(f.url).then((res) => res.blob());
        return new File([fileBlob], f.filename as string, {
          type: fileBlob.type,
        });
      } catch (err) {
        console.error(`Error processing file ${f.filename}:`, err);
        return null;
      }
    }
    return null;
  });

  return filePromises;
}

export async function createFormDataWithFiles(
  userInput: string,
  sessionId: string,
  message: PromptInputMessage | undefined
) {
  const formData = new FormData();
  formData.append("input", userInput);
  formData.append("session_id", sessionId);
  let filePromises;

  if (message?.files && message.files.length > 0) {
    filePromises = await createFileInterfaces(message.files);
  }

  const files = (await Promise.all(filePromises ?? [])).filter(
    (file): file is File => file !== null
  );

  if (files.length > 0) {
    files.forEach((file) => {
      formData.append("files", file, file.name);
    });
  }

  return formData;
}

export async function streamParser<T>(
  response: Response,
  onEvent: (data: T) => void
) {
  const reader = response.body?.getReader();
  if (!reader) throw new Error("Response body is not readable");

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();

    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    const events = buffer.split("\n\n");

    buffer = events.pop() ?? "";

    for (const rawEvent of events) {
      // TODO: Extend this with the new type of datas
      if (!rawEvent.startsWith("data:")) continue;
      const jsonString = rawEvent.replace(/^data:\s*/, "");

      try {
        const parsed = JSON.parse(jsonString) as T;
        onEvent(parsed);
      } catch (err) {
        console.error("Failed to parse SSE event:", jsonString, err);
      }
    }
  }
}
