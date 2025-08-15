import { NextResponse } from "next/server";
import { writeFile, mkdtemp, rm } from "fs/promises";
import os from "os";
import path from "path";
import { spawn } from "child_process";

async function runBridge(args: string[], stdinData?: string) {
  const frontendRoot = process.cwd();
  const backendRoot = path.resolve(frontendRoot, "../backend");
  const pyPath = process.env.PYTHON_PATH || "python3";
  const cmd = spawn(pyPath, [path.join(backendRoot, "api_bridge.py"), ...args], {
    cwd: backendRoot,
  });

  let stdout = "";
  let stderr = "";
  cmd.stdout.on("data", (d) => (stdout += d.toString()));
  cmd.stderr.on("data", (d) => (stderr += d.toString()));
  if (stdinData) {
    cmd.stdin.write(stdinData);
    cmd.stdin.end();
  }
  await new Promise<void>((resolve) => cmd.on("close", () => resolve()));
  try {
    return JSON.parse(stdout.trim());
  } catch (e) {
    return { error: stderr || stdout || "Unknown error" };
  }
}

export async function POST(req: Request) {
  try {
    const contentType = req.headers.get("content-type") || "";
    const frontendRoot = process.cwd();
    const backendRoot = path.resolve(frontendRoot, "../backend");
    const cldrPath = path.join(backendRoot, "cldr_data");

    if (contentType.includes("multipart/form-data")) {
      const form = await req.formData();
      const mode = String(form.get("mode"));

      const tempDir = await mkdtemp(path.join(os.tmpdir(), "lexray-"));
      const tempFiles: string[] = [];
      const saveFile = async (file: File, name: string) => {
        const buffer = Buffer.from(await file.arrayBuffer());
        const filePath = path.join(tempDir, name);
        await writeFile(filePath, buffer);
        tempFiles.push(filePath);
        return filePath;
      };

      let result: any;
      if (mode === "batch-english") {
        const csv = form.get("csv") as File;
        const csvPath = await saveFile(csv, "english.csv");
        result = await runBridge(["batch-english", "--csv", csvPath, "--cldr_path", cldrPath]);
      } else if (mode === "batch-cldr") {
        const lang = String(form.get("language"));
        const csv = form.get("csv") as File;
        const csvPath = await saveFile(csv, "pairs.csv");
        result = await runBridge(["batch-cldr", "--csv", csvPath, "--language", lang, "--cldr_path", cldrPath]);
      } else if (mode === "batch-noncldr") {
        const lang = String(form.get("language"));
        const pairs = form.get("pairs_csv") as File;
        const elements = form.get("elements_csv") as File;
        const pairsPath = await saveFile(pairs, "pairs.csv");
        const elementsPath = await saveFile(elements, "elements.csv");
        result = await runBridge([
          "batch-noncldr",
          "--pairs_csv",
          pairsPath,
          "--elements_csv",
          elementsPath,
          "--language",
          lang,
          "--cldr_path",
          cldrPath,
        ]);
      } else if (mode === "single-english") {
        const english = String(form.get("english"));
        result = await runBridge(["single-english", "--english", english, "--cldr_path", cldrPath]);
      } else if (mode === "single-cldr") {
        const english = String(form.get("english"));
        const language = String(form.get("language"));
        const translation = String(form.get("translation"));
        result = await runBridge([
          "single-cldr",
          "--english",
          english,
          "--language",
          language,
          "--translation",
          translation,
          "--cldr_path",
          cldrPath,
        ]);
      } else if (mode === "single-new") {
        const english = String(form.get("english"));
        const language = String(form.get("language"));
        const translation = String(form.get("translation"));
        const elements = form.get("elements_csv") as File;
        const elementsPath = await saveFile(elements, "elements.csv");
        result = await runBridge([
          "single-new",
          "--english",
          english,
          "--language",
          language,
          "--translation",
          translation,
          "--elements_csv",
          elementsPath,
          "--cldr_path",
          cldrPath,
        ]);
      } else {
        result = { error: "Unknown mode" };
      }

      // Cleanup temp files
      await rm(tempDir, { recursive: true, force: true });
      return NextResponse.json(result);
    }

    // Fallback
    return NextResponse.json({ error: "Unsupported content type" }, { status: 400 });
  } catch (e: any) {
    return NextResponse.json({ error: e?.message || String(e) }, { status: 500 });
  }
}


