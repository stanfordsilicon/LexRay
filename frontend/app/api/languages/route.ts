import { NextResponse } from "next/server";
import { readdir } from "fs/promises";
import path from "path";

// GET /api/languages → returns list of languages that have *_moderate.xlsx in backend/cldr_data
export async function GET() {
  try {
    const frontendRoot = process.cwd();
    const cldrDir = path.resolve(frontendRoot, "../backend/cldr_data");
    const entries = await readdir(cldrDir, { withFileTypes: true });

    const languages: string[] = entries
      .filter((d) => d.isFile() && /_moderate\.xlsx$/i.test(d.name))
      .map((d) => d.name.replace(/_moderate\.xlsx$/i, ""))
      .filter((name) => name.toLowerCase() !== "english")
      .sort((a, b) => a.localeCompare(b));

    return NextResponse.json({ languages });
  } catch (error) {
    return NextResponse.json(
      { languages: [], error: "Could not read CLDR languages" },
      { status: 200 }
    );
  }
}


