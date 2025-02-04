import { Persona } from "@/app/admin/assistants/interfaces";

interface DiscordChannelConfigCreationRequest {
  discord_bot_id: number;
  document_sets: number[];
  persona_id: number | null;
  enable_auto_filters: boolean;
  channel_name: string;
  answer_validity_check_enabled: boolean;
  questionmark_prefilter_enabled: boolean;
  respond_mention_only: boolean;
  respond_to_bots: boolean;
  show_continue_in_web_ui: boolean;
  respond_member_group_list: string[];
  follow_up_tags?: string[];
  usePersona: boolean;
}

const buildFiltersFromCreationRequest = (
  creationRequest: DiscordChannelConfigCreationRequest
): string[] => {
  const answerFilters = [] as string[];
  if (creationRequest.answer_validity_check_enabled) {
    answerFilters.push("well_answered_postfilter");
  }
  if (creationRequest.questionmark_prefilter_enabled) {
    answerFilters.push("questionmark_prefilter");
  }
  return answerFilters;
};

const buildRequestBodyFromCreationRequest = (
  creationRequest: DiscordChannelConfigCreationRequest
) => {
  return JSON.stringify({
    discord_bot_id: creationRequest.discord_bot_id,
    channel_name: creationRequest.channel_name,
    respond_mention_only: creationRequest.respond_mention_only,
    respond_to_bots: creationRequest.respond_to_bots,
    show_continue_in_web_ui: creationRequest.show_continue_in_web_ui,
    enable_auto_filters: creationRequest.enable_auto_filters,
    respond_member_group_list: creationRequest.respond_member_group_list,
    answer_filters: buildFiltersFromCreationRequest(creationRequest),
    follow_up_tags: creationRequest.follow_up_tags?.filter((tag) => tag !== ""),
    ...(creationRequest.usePersona
      ? { persona_id: creationRequest.persona_id }
      : { document_sets: creationRequest.document_sets }),
  });
};

export const createDiscordChannelConfig = async (
  creationRequest: DiscordChannelConfigCreationRequest
) => {
  return fetch("/api/manage/admin/discord-app/channel", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: buildRequestBodyFromCreationRequest(creationRequest),
  });
};

export const updateDiscordChannelConfig = async (
  id: number,
  creationRequest: DiscordChannelConfigCreationRequest
) => {
  return fetch(`/api/manage/admin/discord-app/channel/${id}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: buildRequestBodyFromCreationRequest(creationRequest),
  });
};

export const deleteDiscordChannelConfig = async (id: number) => {
  return fetch(`/api/manage/admin/discord-app/channel/${id}`, {
    method: "DELETE",
    headers: {
      "Content-Type": "application/json",
    },
  });
};

export function isPersonaADiscordBotPersona(persona: Persona) {
  return persona.name.startsWith("__discord_bot_persona__");
}
