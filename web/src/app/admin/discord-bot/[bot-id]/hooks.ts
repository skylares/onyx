import { errorHandlingFetcher } from "@/lib/fetcher";
import { DiscordBot, DiscordChannelConfig } from "@/lib/types";
import useSWR, { mutate } from "swr";

export const useDiscordChannelConfigs = () => {
  const url = "/api/manage/admin/discord-app/channel";
  const swrResponse = useSWR<DiscordChannelConfig[]>(url, errorHandlingFetcher);

  return {
    ...swrResponse,
    refreshDiscordChannelConfigs: () => mutate(url),
  };
};

export const useDiscordBots = () => {
  const url = "/api/manage/admin/discord-app/bots";
  const swrResponse = useSWR<DiscordBot[]>(url, errorHandlingFetcher);

  return {
    ...swrResponse,
    refreshDiscordBots: () => mutate(url),
  };
};

export const useDiscordBot = (botId: number) => {
  const url = `/api/manage/admin/discord-app/bots/${botId}`;
  const swrResponse = useSWR<DiscordBot>(url, errorHandlingFetcher);

  return {
    ...swrResponse,
    refreshDiscordBot: () => mutate(url),
  };
};

export const useDiscordChannelConfigsByBot = (botId: number) => {
  const url = `/api/manage/admin/discord-app/bots/${botId}/config`;
  const swrResponse = useSWR<DiscordChannelConfig[]>(url, errorHandlingFetcher);

  return {
    ...swrResponse,
    refreshDiscordChannelConfigs: () => mutate(url),
  };
};
