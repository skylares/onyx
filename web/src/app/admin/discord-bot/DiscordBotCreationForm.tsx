"use client";

import CardSection from "@/components/admin/CardSection";
import { usePopup } from "@/components/admin/connectors/Popup";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { DiscordTokensForm } from "./DiscordTokensForm";
import { SourceIcon } from "@/components/SourceIcon";
import { AdminPageTitle } from "@/components/admin/Title";
import { ValidSources } from "@/lib/types";

export const NewDiscordBotForm = () => {
  const [formValues] = useState({
    name: "",
    enabled: true,
    bot_token: "",
  });
  const { popup, setPopup } = usePopup();
  const router = useRouter();

  return (
    <div>
      <AdminPageTitle
        icon={<SourceIcon iconSize={36} sourceType={ValidSources.Discord} />}
        title="New Discord Bot"
      />
      <CardSection>
        {popup}
        <div className="p-4">
          <DiscordTokensForm
            isUpdate={false}
            initialValues={formValues}
            setPopup={setPopup}
            router={router}
          />
        </div>
      </CardSection>
    </div>
  );
};
