import { AdminPageTitle } from "@/components/admin/Title";
import { DiscordChannelConfigCreationForm } from "../DiscordChannelConfigCreationForm";
import { fetchSS } from "@/lib/utilsSS";
import { ErrorCallout } from "@/components/ErrorCallout";
import { DocumentSet, ValidSources } from "@/lib/types";
import { BackButton } from "@/components/BackButton";
import { fetchAssistantsSS } from "@/lib/assistants/fetchAssistantsSS";
import {
  getStandardAnswerCategoriesIfEE,
  StandardAnswerCategoryResponse,
} from "@/components/standardAnswers/getStandardAnswerCategoriesIfEE";
import { redirect } from "next/navigation";
import { Persona } from "../../../../assistants/interfaces";
import { SourceIcon } from "@/components/SourceIcon";

async function NewChannelConfigPage(props: {
  params: Promise<{ "bot-id": string }>;
}) {
  const unwrappedParams = await props.params;
  const discord_bot_id_raw = unwrappedParams?.["bot-id"] || null;
  const discord_bot_id = discord_bot_id_raw
    ? parseInt(discord_bot_id_raw as string, 10)
    : null;
  if (!discord_bot_id || isNaN(discord_bot_id)) {
    redirect("/admin/discord-bot");
    return null;
  }

  const [
    documentSetsResponse,
    assistantsResponse,
    standardAnswerCategoryResponse,
  ] = await Promise.all([
    fetchSS("/manage/document-set") as Promise<Response>,
    fetchAssistantsSS() as Promise<[Persona[], string | null]>,
    getStandardAnswerCategoriesIfEE() as Promise<StandardAnswerCategoryResponse>,
  ]);

  if (!documentSetsResponse.ok) {
    return (
      <ErrorCallout
        errorTitle="Something went wrong :("
        errorMsg={`Failed to fetch document sets - ${await documentSetsResponse.text()}`}
      />
    );
  }
  const documentSets = (await documentSetsResponse.json()) as DocumentSet[];

  if (assistantsResponse[1]) {
    return (
      <ErrorCallout
        errorTitle="Something went wrong :("
        errorMsg={`Failed to fetch assistants - ${assistantsResponse[1]}`}
      />
    );
  }

  return (
    <div className="container mx-auto">
      <BackButton />
      <AdminPageTitle
        icon={<SourceIcon iconSize={32} sourceType={ValidSources.Discord} />}
        title="Configure OnyxBot for Discord Channel"
      />

      <DiscordChannelConfigCreationForm
        discord_bot_id={discord_bot_id}
        documentSets={documentSets}
        personas={assistantsResponse[0]}
      />
    </div>
  );
}

export default NewChannelConfigPage;
