const SERVICE = "investment-report-dispatcher";
const TORONTO_TZ = "America/Toronto";

export default {
  async fetch(request, env, ctx) {
    return handleRequest(request, env, ctx);
  },

  async scheduled(event, env, ctx) {
    ctx.waitUntil(handleScheduled(event, env));
  },
};

async function handleScheduled(event, env) {
  const executionDate = new Date();
  const scheduledDate = event.scheduledTime
    ? new Date(event.scheduledTime)
    : executionDate;
  const toronto = getTorontoParts(scheduledDate);
  const routing = chooseScheduledTarget(event.cron, toronto);
  console.log(JSON.stringify({
    service: SERVICE,
    type: "scheduled",
    cron: event.cron,
    executionTimeUtc: executionDate.toISOString(),
    scheduledTimeUtc: scheduledDate.toISOString(),
    toronto,
    target: routing.target,
    skipReason: routing.skipReason,
  }));

  if (!toronto.isWeekday) {
    console.log("Skipped scheduled dispatch on Toronto weekend.");
    return;
  }

  if (!routing.target) {
    console.log(`Skipped scheduled dispatch: ${routing.skipReason}`);
    return;
  }

  const workflowId = routing.target === "daily" ? env.DAILY_WORKFLOW_ID : env.HUB_WORKFLOW_ID;
  const payload = buildWorkflowPayload(routing.target, toronto.date, env);
  const result = await dispatchWorkflow(env, workflowId, payload.inputs);
  console.log(JSON.stringify({
    service: SERVICE,
    target: routing.target,
    date: toronto.date,
    workflowId,
    githubStatus: result.status,
    ok: result.ok,
    body: result.body,
  }));
}

async function handleRequest(request, env) {
  const url = new URL(request.url);

  if (request.method !== "GET") {
    return jsonResponse({ ok: false, error: "method_not_allowed" }, 405);
  }

  if (url.pathname === "/health") {
    return jsonResponse({ ok: true, service: SERVICE });
  }

  if (url.pathname === "/debug-time") {
    return jsonResponse({
      ok: true,
      service: SERVICE,
      now_utc: new Date().toISOString(),
      toronto_now: getTorontoParts(new Date()),
      expected_crons: {
        daily: ["15 12 * * 1-5", "15 13 * * 1-5"],
        hub: ["30 12 * * 1-5", "30 13 * * 1-5"],
      },
      note: "Scheduled dispatch routing uses event.scheduledTime, not wall-clock execution time.",
    });
  }

  if (url.pathname === "/dispatch") {
    return handleManualDispatch(request, url, env);
  }

  return jsonResponse({ ok: false, error: "not_found" }, 404);
}

async function handleManualDispatch(request, url, env) {
  const target = url.searchParams.get("target");
  const date = url.searchParams.get("date") || getTorontoParts(new Date()).date;
  const dryRun = url.searchParams.get("dry_run") === "true";

  if (!["daily", "hub"].includes(target)) {
    return jsonResponse({ ok: false, error: "invalid_target", allowed: ["daily", "hub"] }, 400);
  }

  if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) {
    return jsonResponse({ ok: false, error: "invalid_date", expected: "YYYY-MM-DD" }, 400);
  }

  const workflowId = target === "daily" ? env.DAILY_WORKFLOW_ID : env.HUB_WORKFLOW_ID;
  const payload = buildWorkflowPayload(target, date, env);

  if (dryRun) {
    return jsonResponse({
      ok: true,
      dry_run: true,
      target,
      workflow_id: workflowId,
      payload,
    });
  }

  const providedSecret = request.headers.get("X-Dispatch-Secret") || "";
  if (!env.DISPATCH_SECRET || providedSecret !== env.DISPATCH_SECRET) {
    return jsonResponse({ ok: false, error: "unauthorized" }, 401);
  }

  const result = await dispatchWorkflow(env, workflowId, payload.inputs);
  return jsonResponse({
    ok: result.ok,
    target,
    workflow_id: workflowId,
    github_status: result.status,
    github_body: result.body,
  }, result.ok ? 200 : 502);
}

function getTorontoParts(date) {
  const formatter = new Intl.DateTimeFormat("en-CA", {
    timeZone: TORONTO_TZ,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    weekday: "short",
    hourCycle: "h23",
  });

  const parts = Object.fromEntries(
    formatter.formatToParts(date)
      .filter((part) => part.type !== "literal")
      .map((part) => [part.type, part.value])
  );
  const weekday = parts.weekday;
  return {
    date: `${parts.year}-${parts.month}-${parts.day}`,
    time: `${parts.hour}:${parts.minute}`,
    weekday,
    isWeekday: !["Sat", "Sun"].includes(weekday),
  };
}

function chooseScheduledTarget(cron, torontoParts) {
  if (!torontoParts.isWeekday) {
    return { target: null, skipReason: "toronto_weekend" };
  }

  if (cron === "15 12 * * 1-5" || cron === "15 13 * * 1-5") {
    if (torontoParts.time === "08:15") {
      return { target: "daily", skipReason: null };
    }
    return {
      target: null,
      skipReason: `daily cron fired, but scheduled Toronto time was ${torontoParts.time}, not 08:15`,
    };
  }

  if (cron === "30 12 * * 1-5" || cron === "30 13 * * 1-5") {
    if (torontoParts.time === "08:30") {
      return { target: "hub", skipReason: null };
    }
    return {
      target: null,
      skipReason: `hub cron fired, but scheduled Toronto time was ${torontoParts.time}, not 08:30`,
    };
  }

  return { target: null, skipReason: `unrecognized cron expression: ${cron}` };
}

function buildWorkflowPayload(target, date, env) {
  if (target === "daily") {
    return {
      ref: env.GITHUB_REF || "main",
      inputs: {},
    };
  }

  return {
    ref: env.GITHUB_REF || "main",
    inputs: {
      date,
      mode: "parallel",
      publish: "true",
    },
  };
}

async function dispatchWorkflow(env, workflowId, inputs) {
  const owner = env.GITHUB_OWNER || "robinyew";
  const repo = env.GITHUB_REPO || "ai-investing-monitor";
  const ref = env.GITHUB_REF || "main";
  const url = `https://api.github.com/repos/${owner}/${repo}/actions/workflows/${encodeURIComponent(workflowId)}/dispatches`;
  const body = JSON.stringify({ ref, inputs: inputs || {} });

  const response = await fetch(url, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${env.GITHUB_WORKFLOW_TOKEN}`,
      Accept: "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28",
      "User-Agent": SERVICE,
      "Content-Type": "application/json",
    },
    body,
  });

  const responseText = await response.text();
  return {
    ok: response.ok,
    status: response.status,
    body: responseText,
  };
}

function jsonResponse(data, status = 200) {
  return new Response(JSON.stringify(data, null, 2), {
    status,
    headers: {
      "Content-Type": "application/json",
    },
  });
}
