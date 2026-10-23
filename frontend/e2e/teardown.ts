import { execFileSync } from "node:child_process";

export default function teardown() {
  // Windows can terminate the server without running Python's finally block.
  execFileSync(
    process.env.PYTHON || "python",
    ["../scripts/run_e2e_api.py", "--cleanup"],
    { stdio: "inherit" },
  );
}
