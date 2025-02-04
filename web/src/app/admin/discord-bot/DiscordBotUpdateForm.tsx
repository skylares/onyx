"use client";

import { usePopup } from "@/components/admin/connectors/Popup";
import { DiscordBot, ValidSources } from "@/lib/types";
import { useRouter } from "next/navigation";
import { ChevronDown, ChevronRight } from "lucide-react";
import { useState, useEffect, useRef } from "react";
import { updateDiscordBotField } from "@/lib/updateDiscordBotField";
import { Checkbox } from "@/app/admin/settings/SettingsForm";
import { DiscordTokensForm } from "./DiscordTokensForm";
import { SourceIcon } from "@/components/SourceIcon";
import { EditableStringFieldDisplay } from "@/components/EditableStringFieldDisplay";
import { deleteDiscordBot } from "./new/lib";
import { GenericConfirmModal } from "@/components/modals/GenericConfirmModal";
import { FiTrash } from "react-icons/fi";
import { Button } from "@/components/ui/button";

export const ExistingDiscordBotForm = ({
  existingDiscordBot,
  refreshDiscordBot,
}: {
  existingDiscordBot: DiscordBot;
  refreshDiscordBot?: () => void;
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [formValues, setFormValues] = useState(existingDiscordBot);
  const { popup, setPopup } = usePopup();
  const router = useRouter();
  const dropdownRef = useRef<HTMLDivElement>(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);

  const handleUpdateField = async (
    field: keyof DiscordBot,
    value: string | boolean
  ) => {
    try {
      const response = await updateDiscordBotField(
        existingDiscordBot,
        field,
        value
      );
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setPopup({
        message: `Connector ${field} updated successfully`,
        type: "success",
      });
    } catch (error) {
      setPopup({
        message: `Failed to update connector ${field}`,
        type: "error",
      });
    }
    setFormValues((prev) => ({ ...prev, [field]: value }));
  };

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node) &&
        isExpanded
      ) {
        setIsExpanded(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isExpanded]);

  return (
    <div>
      {popup}
      <div className="flex items-center justify-between h-14">
        <div className="flex items-center gap-2">
          <div className="my-auto">
            <SourceIcon iconSize={32} sourceType={ValidSources.Discord} />
          </div>
          <div className="ml-1">
            <EditableStringFieldDisplay
              value={formValues.name}
              isEditable={true}
              onUpdate={(value) => handleUpdateField("name", value)}
              scale={2.1}
            />
          </div>
        </div>

        <div className="flex flex-col" ref={dropdownRef}>
          <div className="flex items-center gap-4">
            <div className="border rounded-lg border-gray-200">
              <div
                className="flex items-center gap-2 cursor-pointer hover:bg-gray-100 p-2"
                onClick={() => setIsExpanded(!isExpanded)}
              >
                {isExpanded ? (
                  <ChevronDown size={20} />
                ) : (
                  <ChevronRight size={20} />
                )}
                <span>Update Token</span>
              </div>
            </div>
            <Button
              variant="destructive"
              onClick={() => setShowDeleteModal(true)}
              icon={FiTrash}
              tooltip="Click to delete"
              className="border h-[42px]"
            >
              Delete
            </Button>
          </div>

          {isExpanded && (
            <div className="bg-white border rounded-lg border-gray-200 shadow-lg absolute mt-12 right-0 z-10 w-full md:w-3/4 lg:w-1/2">
              <div className="p-4">
                <DiscordTokensForm
                  isUpdate={true}
                  initialValues={formValues}
                  existingDiscordBotId={existingDiscordBot.id}
                  refreshDiscordBot={refreshDiscordBot}
                  setPopup={setPopup}
                  router={router}
                  onValuesChange={(values) => setFormValues(values)}
                />
              </div>
            </div>
          )}
        </div>
      </div>
      <div className="mt-2">
        <div className="inline-block border rounded-lg border-gray-200 p-2">
          <Checkbox
            label="Enabled"
            checked={formValues.enabled}
            onChange={(e) => handleUpdateField("enabled", e.target.checked)}
          />
        </div>
        {showDeleteModal && (
          <GenericConfirmModal
            title="Delete Discord Bot"
            message="Are you sure you want to delete this Discord bot? This action cannot be undone."
            confirmText="Delete"
            onClose={() => setShowDeleteModal(false)}
            onConfirm={async () => {
              try {
                const response = await deleteDiscordBot(existingDiscordBot.id);
                if (!response.ok) {
                  throw new Error(await response.text());
                }
                setPopup({
                  message: "Discord bot deleted successfully",
                  type: "success",
                });
                router.push("/admin/discord-bot");
              } catch (error) {
                setPopup({
                  message: "Failed to delete Discord bot",
                  type: "error",
                });
              }
              setShowDeleteModal(false);
            }}
          />
        )}
      </div>
    </div>
  );
};
