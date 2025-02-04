"use client";

import { ErrorCallout } from "@/components/ErrorCallout";
import { FiPlusSquare } from "react-icons/fi";
import { ThreeDotsLoader } from "@/components/Loading";
import { InstantSSRAutoRefresh } from "@/components/SSRAutoRefresh";
import { AdminPageTitle } from "@/components/admin/Title";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { SourceIcon } from "@/components/SourceIcon";
import { DiscordBotTable } from "./DiscordBotTable";
import { useDiscordBots } from "./[bot-id]/hooks";
import { ValidSources } from "@/lib/types";

const Main = () => {
  const {
    data: discordBots,
    isLoading: isDiscordBotsLoading,
    error: discordBotsError,
  } = useDiscordBots();

  if (isDiscordBotsLoading) {
    return <ThreeDotsLoader />;
  }

  if (discordBotsError || !discordBots) {
    const errorMsg =
      discordBotsError?.info?.message ||
      discordBotsError?.info?.detail ||
      "An unknown error occurred";

    return (
      <ErrorCallout errorTitle="Error loading apps" errorMsg={`${errorMsg}`} />
    );
  }

  return (
    <div className="mb-8">
      {/* {popup} */}

      <p className="mb-2 text-sm text-muted-foreground">
        Setup Discord bots that connect to Onyx. Once setup, you will be able to
        ask questions to Onyx directly from Discord. Additionally, you can:
      </p>

      <div className="mb-2">
        <ul className="list-disc mt-2 ml-4 text-sm text-muted-foreground">
          <li>
            Setup OnyxBot to automatically answer questions in certain channels.
          </li>
          <li>
            Choose which document sets OnyxBot should answer from, depending on
            the channel the question is being asked.
          </li>
          <li>
            Directly message OnyxBot to search just as you would in the web UI.
          </li>
        </ul>
      </div>

      <p className="mb-6 text-sm text-muted-foreground">
        Follow the{" "}
        <a
          className="text-blue-500 hover:underline"
          href="https://docs.onyx.app/discord_bot_setup"
          target="_blank"
          rel="noopener noreferrer"
        >
          guide{" "}
        </a>
        found in the Onyx documentation to get started!
      </p>

      <Link
        className="
            inline-flex
            py-2
            px-4
            mt-2
            border
            border-border
            h-fit
            cursor-pointer
            hover:bg-hover
            text-sm
            w-45
          "
        href="/admin/discord-bot/new"
      >
        <div className="flex">
          <FiPlusSquare className="my-auto mr-2" />
          New Discord Bot
        </div>
      </Link>

      <DiscordBotTable discordBots={discordBots} />
    </div>
  );
};

const Page = () => {
  return (
    <div className="container mx-auto">
      <AdminPageTitle
        icon={<SourceIcon iconSize={36} sourceType={ValidSources.Discord} />}
        title="Discord Bots"
      />
      <InstantSSRAutoRefresh />

      <Main />
    </div>
  );
};

export default Page;
