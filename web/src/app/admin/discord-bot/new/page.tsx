import { BackButton } from "@/components/BackButton";
import { NewDiscordBotForm } from "../DiscordBotCreationForm";

async function NewDiscordBotPage() {
  return (
    <div className="container mx-auto">
      <BackButton routerOverride="/admin/discord-bot" />

      <NewDiscordBotForm />
    </div>
  );
}

export default NewDiscordBotPage;
