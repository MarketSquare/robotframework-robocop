// Runs release-please (the same way as googleapis/release-please-action) with a custom versioning strategy.
//
// The default strategy bumps the major version for breaking changes, the minor version for `feat` and the patch
// version for everything else. The `perf-bumps-minor` strategy (selected with `versioning` in
// release-please-config.json) also bumps the minor version for `perf` commits.
//
// Usage: node .github/scripts/release-please.cjs [--dry-run]
// Requires GITHUB_TOKEN and GITHUB_REPOSITORY environment variables. With --dry-run, only prints the release pull
// requests that would be created.
const fs = require("node:fs");
const { GitHub, Manifest, registerVersioningStrategy } = require("release-please");
const { DefaultVersioningStrategy } = require("release-please/build/src/versioning-strategies/default");
const { MinorVersionUpdate, PatchVersionUpdate } = require("release-please/build/src/versioning-strategy");

const CONFIG_FILE = "release-please-config.json";
const MANIFEST_FILE = ".release-please-manifest.json";

class PerfBumpsMinorVersioningStrategy extends DefaultVersioningStrategy {
  determineReleaseType(version, commits) {
    const update = super.determineReleaseType(version, commits);
    if (update instanceof PatchVersionUpdate && commits.some((commit) => commit.type === "perf")) {
      return new MinorVersionUpdate();
    }
    return update;
  }
}

registerVersioningStrategy("perf-bumps-minor", (options) => new PerfBumpsMinorVersioningStrategy(options));

function setOutputs(outputs) {
  if (!process.env.GITHUB_OUTPUT) {
    return;
  }
  const lines = Object.entries(outputs).map(([key, value]) => `${key}=${value}\n`);
  fs.appendFileSync(process.env.GITHUB_OUTPUT, lines.join(""));
}

async function main() {
  const [owner, repo] = (process.env.GITHUB_REPOSITORY || "").split("/");
  const github = await GitHub.create({ owner, repo, token: process.env.GITHUB_TOKEN });
  const loadManifest = () =>
    Manifest.fromManifest(github, github.repository.defaultBranch, CONFIG_FILE, MANIFEST_FILE);

  if (process.argv.includes("--dry-run")) {
    for (const pullRequest of await (await loadManifest()).buildPullRequests()) {
      console.log(pullRequest.title.toString());
    }
    return;
  }

  const releases = (await (await loadManifest()).createReleases()).filter(Boolean);
  const rootRelease = releases.find((release) => (release.path || ".") === ".");
  setOutputs({ releases_created: releases.length > 0 });
  if (rootRelease) {
    setOutputs({ release_created: true, tag_name: rootRelease.tagName });
  }

  const pullRequests = (await (await loadManifest()).createPullRequests()).filter(Boolean);
  setOutputs({ prs_created: pullRequests.length > 0 });
}

main().catch((error) => {
  console.error(`release-please failed: ${error.message}`);
  process.exitCode = 1;
});
