import { redirect } from "next/navigation";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/authOptions";

export default async function RootPage() {
  const session = await getServerSession(authOptions);
  redirect(session ? "/schedule" : "/login");
}
