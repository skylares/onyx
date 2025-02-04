import { DiscordBot } from "@/lib/types";

export async function updateDiscordBotField(
  discordBot: DiscordBot,
  field: keyof DiscordBot,
  value: any
): Promise<Response> {
  return fetch(`/api/manage/admin/discord-app/bots/${discordBot.id}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      ...discordBot,
      [field]: value,
    }),
  });
}
