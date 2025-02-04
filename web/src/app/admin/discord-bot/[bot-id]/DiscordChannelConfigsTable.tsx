"use client";

import { PageSelector } from "@/components/PageSelector";
import { PopupSpec } from "@/components/admin/connectors/Popup";
import { EditIcon, TrashIcon } from "@/components/icons/icons";
import { DiscordChannelConfig } from "@/lib/types";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import Link from "next/link";
import { useState } from "react";
import { deleteDiscordChannelConfig, isPersonaADiscordBotPersona } from "./lib";

const numToDisplay = 50;

export function DiscordChannelConfigsTable({
  discordBotId,
  discordChannelConfigs,
  refresh,
  setPopup,
}: {
  discordBotId: number;
  discordChannelConfigs: DiscordChannelConfig[];
  refresh: () => void;
  setPopup: (popupSpec: PopupSpec | null) => void;
}) {
  const [page, setPage] = useState(1);

  // sort by name for consistent ordering
  discordChannelConfigs.sort((a, b) => {
    if (a.id < b.id) {
      return -1;
    } else if (a.id > b.id) {
      return 1;
    } else {
      return 0;
    }
  });

  return (
    <div>
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Channel</TableHead>
              <TableHead>Assistant</TableHead>
              <TableHead>Document Sets</TableHead>
              <TableHead>Delete</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {discordChannelConfigs
              .slice(numToDisplay * (page - 1), numToDisplay * page)
              .map((discordChannelConfig) => {
                return (
                  <TableRow
                    key={discordChannelConfig.id}
                    className="cursor-pointer hover:bg-gray-100 transition-colors"
                    onClick={() => {
                      window.location.href = `/admin/discord-bot/${discordBotId}/channels/${discordChannelConfig.id}`;
                    }}
                  >
                    <TableCell>
                      <div className="flex gap-x-2">
                        <div className="my-auto">
                          <EditIcon />
                        </div>
                        <div className="my-auto">
                          {"#" +
                            discordChannelConfig.channel_config.channel_name}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell onClick={(e) => e.stopPropagation()}>
                      {discordChannelConfig.persona &&
                      !isPersonaADiscordBotPersona(
                        discordChannelConfig.persona
                      ) ? (
                        <Link
                          href={`/admin/assistants/${discordChannelConfig.persona.id}`}
                          className="text-blue-500 flex hover:underline"
                        >
                          {discordChannelConfig.persona.name}
                        </Link>
                      ) : (
                        "-"
                      )}
                    </TableCell>
                    <TableCell>
                      <div>
                        {discordChannelConfig.persona &&
                        discordChannelConfig.persona.document_sets.length > 0
                          ? discordChannelConfig.persona.document_sets
                              .map((documentSet) => documentSet.name)
                              .join(", ")
                          : "-"}
                      </div>
                    </TableCell>
                    <TableCell onClick={(e) => e.stopPropagation()}>
                      <div
                        className="cursor-pointer hover:text-destructive"
                        onClick={async (e) => {
                          e.stopPropagation();
                          const response = await deleteDiscordChannelConfig(
                            discordChannelConfig.id
                          );
                          if (response.ok) {
                            setPopup({
                              message: `Discord bot config "${discordChannelConfig.id}" deleted`,
                              type: "success",
                            });
                          } else {
                            const errorMsg = await response.text();
                            setPopup({
                              message: `Failed to delete Discord bot config - ${errorMsg}`,
                              type: "error",
                            });
                          }
                          refresh();
                        }}
                      >
                        <TrashIcon />
                      </div>
                    </TableCell>
                  </TableRow>
                );
              })}

            {/* Empty row with message when table has no data */}
            {discordChannelConfigs.length === 0 && (
              <TableRow>
                <TableCell
                  colSpan={4}
                  className="text-center text-muted-foreground"
                >
                  Please add a New Discord Bot Configuration to begin chatting
                  with Onyx!
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      <div className="mt-3 flex">
        <div className="mx-auto">
          <PageSelector
            totalPages={Math.ceil(discordChannelConfigs.length / numToDisplay)}
            currentPage={page}
            onPageChange={(newPage) => setPage(newPage)}
          />
        </div>
      </div>
    </div>
  );
}
