"use client";

import { use } from "react";
import { BackButton } from "@/components/BackButton";
import { ErrorCallout } from "@/components/ErrorCallout";
import { ThreeDotsLoader } from "@/components/Loading";
import { InstantSSRAutoRefresh } from "@/components/SSRAutoRefresh";
import { usePopup } from "@/components/admin/connectors/Popup";
import Link from "next/link";
import { DiscordChannelConfigsTable } from "./DiscordChannelConfigsTable";
import { useDiscordBot, useDiscordChannelConfigsByBot } from "./hooks";
import { ExistingDiscordBotForm } from "@/app/admin/discord-bot/DiscordBotUpdateForm";
import { FiPlusSquare } from "react-icons/fi";
import { Separator } from "@/components/ui/separator";

function DiscordBotEditPage({
  params,
}: {
  params: Promise<{ "bot-id": string }>;
}) {
  // Unwrap the params promise
  const unwrappedParams = use(params);
  const { popup, setPopup } = usePopup();

  const {
    data: discordBot,
    isLoading: isDiscordBotLoading,
    error: discordBotError,
    refreshDiscordBot,
  } = useDiscordBot(Number(unwrappedParams["bot-id"]));

  const {
    data: discordChannelConfigs,
    isLoading: isDiscordChannelConfigsLoading,
    error: discordChannelConfigsError,
    refreshDiscordChannelConfigs,
  } = useDiscordChannelConfigsByBot(Number(unwrappedParams["bot-id"]));

  if (isDiscordBotLoading || isDiscordChannelConfigsLoading) {
    return <ThreeDotsLoader />;
  }

  if (discordBotError || !discordBot) {
    const errorMsg =
      discordBotError?.info?.message ||
      discordBotError?.info?.detail ||
      "An unknown error occurred";
    return (
      <ErrorCallout
        errorTitle="Something went wrong :("
        errorMsg={`Failed to fetch Discord Bot ${unwrappedParams["bot-id"]}: ${errorMsg}`}
      />
    );
  }

  if (discordChannelConfigsError || !discordChannelConfigs) {
    const errorMsg =
      discordChannelConfigsError?.info?.message ||
      discordChannelConfigsError?.info?.detail ||
      "An unknown error occurred";
    return (
      <ErrorCallout
        errorTitle="Something went wrong :("
        errorMsg={`Failed to fetch Discord Bot ${unwrappedParams["bot-id"]}: ${errorMsg}`}
      />
    );
  }

  return (
    <div className="container mx-auto">
      <InstantSSRAutoRefresh />

      <BackButton routerOverride="/admin/discord-bot" />

      <ExistingDiscordBotForm
        existingDiscordBot={discordBot}
        refreshDiscordBot={refreshDiscordBot}
      />
      <Separator />

      <div className="my-8" />

      <Link
        className="
          flex
          py-2
          px-4
          mt-2
          border
          border-border
          h-fit
          cursor-pointer
          hover:bg-hover
          text-sm
          w-80
        "
        href={`/admin/discord-bot/${unwrappedParams["bot-id"]}/channels/new`}
      >
        <div className="mx-auto flex">
          <FiPlusSquare className="my-auto mr-2" />
          New Discord Channel Configuration
        </div>
      </Link>

      <div className="mt-8">
        <DiscordChannelConfigsTable
          discordBotId={discordBot.id}
          discordChannelConfigs={discordChannelConfigs}
          refresh={refreshDiscordChannelConfigs}
          setPopup={setPopup}
        />
      </div>
    </div>
  );
}

export default DiscordBotEditPage;
