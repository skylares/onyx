import { AdminPageTitle } from "@/components/admin/Title";
import { SourceIcon } from "@/components/SourceIcon";
import { DiscordChannelConfigCreationForm } from "../DiscordChannelConfigCreationForm";
import { fetchSS } from "@/lib/utilsSS";
import { ErrorCallout } from "@/components/ErrorCallout";
import { DocumentSet, DiscordChannelConfig, ValidSources } from "@/lib/types";
import { BackButton } from "@/components/BackButton";
import { InstantSSRAutoRefresh } from "@/components/SSRAutoRefresh";
import {
  FetchAssistantsResponse,
  fetchAssistantsSS,
} from "@/lib/assistants/fetchAssistantsSS";
import { getStandardAnswerCategoriesIfEE } from "@/components/standardAnswers/getStandardAnswerCategoriesIfEE";

async function EditDiscordChannelConfigPage(props: {
  params: Promise<{ id: number }>;
}) {
  const params = await props.params;
  const tasks = [
    fetchSS("/manage/admin/discord-app/channel"),
    fetchSS("/manage/document-set"),
    fetchAssistantsSS(),
  ];

  const [
    discordChannelsResponse,
    documentSetsResponse,
    [assistants, assistantsFetchError],
  ] = (await Promise.all(tasks)) as [
    Response,
    Response,
    FetchAssistantsResponse,
  ];

  const eeStandardAnswerCategoryResponse =
    await getStandardAnswerCategoriesIfEE();

  if (!discordChannelsResponse.ok) {
    return (
      <ErrorCallout
        errorTitle="Something went wrong :("
        errorMsg={`Failed to fetch Discord Channels - ${await discordChannelsResponse.text()}`}
      />
    );
  }
  const allDiscordChannelConfigs =
    (await discordChannelsResponse.json()) as DiscordChannelConfig[];

  const discordChannelConfig = allDiscordChannelConfigs.find(
    (config) => config.id === Number(params.id)
  );

  if (!discordChannelConfig) {
    return (
      <ErrorCallout
        errorTitle="Something went wrong :("
        errorMsg={`Did not find Discord Channel config with ID: ${params.id}`}
      />
    );
  }

  if (!documentSetsResponse.ok) {
    return (
      <ErrorCallout
        errorTitle="Something went wrong :("
        errorMsg={`Failed to fetch document sets - ${await documentSetsResponse.text()}`}
      />
    );
  }
  const documentSets = (await documentSetsResponse.json()) as DocumentSet[];

  if (assistantsFetchError) {
    return (
      <ErrorCallout
        errorTitle="Something went wrong :("
        errorMsg={`Failed to fetch personas - ${assistantsFetchError}`}
      />
    );
  }

  return (
    <div className="container mx-auto">
      <InstantSSRAutoRefresh />

      <BackButton />
      <AdminPageTitle
        icon={<SourceIcon sourceType={ValidSources.Discord} iconSize={32} />}
        title="Edit Discord Channel Config"
      />

      <DiscordChannelConfigCreationForm
        discord_bot_id={discordChannelConfig.discord_bot_id}
        documentSets={documentSets}
        personas={assistants}
        existingDiscordChannelConfig={discordChannelConfig}
      />
    </div>
  );
}

export default EditDiscordChannelConfigPage;
