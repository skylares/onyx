export interface DiscordBotCreationRequest {
  name: string;
  enabled: boolean;
  bot_token: string;
}

const buildRequestBodyFromCreationRequest = (
  creationRequest: DiscordBotCreationRequest
) => {
  return JSON.stringify({
    name: creationRequest.name,
    enabled: creationRequest.enabled,
    bot_token: creationRequest.bot_token,
  });
};

export const createDiscordBot = async (
  creationRequest: DiscordBotCreationRequest
) => {
  return fetch("/api/manage/admin/discord-app/bots", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: buildRequestBodyFromCreationRequest(creationRequest),
  });
};

export const updateDiscordBot = async (
  id: number,
  creationRequest: DiscordBotCreationRequest
) => {
  return fetch(`/api/manage/admin/discord-app/bots/${id}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: buildRequestBodyFromCreationRequest(creationRequest),
  });
};

export const deleteDiscordBot = async (id: number) => {
  return fetch(`/api/manage/admin/discord-app/bots/${id}`, {
    method: "DELETE",
    headers: {
      "Content-Type": "application/json",
    },
  });
};
