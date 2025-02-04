"use client";

import { TextFormField } from "@/components/admin/connectors/Field";
import { Form, Formik } from "formik";
import * as Yup from "yup";
import { createDiscordBot, updateDiscordBot } from "./new/lib";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { useEffect } from "react";

export const DiscordTokensForm = ({
  isUpdate,
  initialValues,
  existingDiscordBotId,
  refreshDiscordBot,
  setPopup,
  router,
  onValuesChange,
}: {
  isUpdate: boolean;
  initialValues: any;
  existingDiscordBotId?: number;
  refreshDiscordBot?: () => void;
  setPopup: (popup: { message: string; type: "error" | "success" }) => void;
  router: any;
  onValuesChange?: (values: any) => void;
}) => {
  useEffect(() => {
    if (onValuesChange) {
      onValuesChange(initialValues);
    }
  }, [initialValues]);

  return (
    <Formik
      initialValues={initialValues}
      validationSchema={Yup.object().shape({
        bot_token: Yup.string().required(),
        name: Yup.string().required(),
      })}
      onSubmit={async (values, formikHelpers) => {
        formikHelpers.setSubmitting(true);

        let response;
        if (isUpdate) {
          response = await updateDiscordBot(existingDiscordBotId!, values);
        } else {
          response = await createDiscordBot(values);
        }
        formikHelpers.setSubmitting(false);
        if (response.ok) {
          if (refreshDiscordBot) {
            refreshDiscordBot();
          }
          const responseJson = await response.json();
          const botId = isUpdate ? existingDiscordBotId : responseJson.id;
          setPopup({
            message: isUpdate
              ? "Successfully updated Discord Bot!"
              : "Successfully created Discord Bot!",
            type: "success",
          });
          router.push(`/admin/discord-bot/${encodeURIComponent(botId)}`);
        } else {
          const responseJson = await response.json();
          const errorMsg = responseJson.detail || responseJson.message;
          setPopup({
            message: isUpdate
              ? `Error updating Discord Bot - ${errorMsg}`
              : `Error creating Discord Bot - ${errorMsg}`,
            type: "error",
          });
        }
      }}
      enableReinitialize={true}
    >
      {({ isSubmitting, setFieldValue, values }) => (
        <Form className="w-full">
          {!isUpdate && (
            <div className="">
              <TextFormField
                name="name"
                label="Name This Discord Bot:"
                type="text"
              />
            </div>
          )}

          {!isUpdate && (
            <div className="mt-4">
              <Separator />
              Please refer to our{" "}
              <a
                className="text-blue-500 hover:underline"
                href="https://docs.onyx.app/discord_bot_setup"
                target="_blank"
                rel="noopener noreferrer"
              >
                guide
              </a>{" "}
              if you are not sure how to get this token!
            </div>
          )}
          <TextFormField
            name="bot_token"
            label="Discord Bot Token"
            type="password"
          />
          <div className="flex justify-end w-full mt-4">
            <Button
              type="submit"
              disabled={isSubmitting || !values.bot_token || !values.name}
              variant="submit"
              size="default"
            >
              {isUpdate ? "Update!" : "Create!"}
            </Button>
          </div>
        </Form>
      )}
    </Formik>
  );
};
