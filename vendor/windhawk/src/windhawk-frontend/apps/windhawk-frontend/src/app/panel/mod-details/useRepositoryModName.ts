import { useCallback, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import useSWR, { useSWRConfig } from 'swr';
import { useGetRepositoryMods } from '@app/webviewIPC';
import type { ModMetadata } from '@app/webviewIPCMessages';

// As much of the host's listing as the names take.
type RepositoryModsListing = Record<
  string,
  { repository: { metadata: ModMetadata } }
>;

// What the cache holds for a language: the name the host's listing carries for
// each mod, or null where the host had no listing to give.
type RepositoryModNames = Record<string, string | undefined> | null;

export type RepositoryModNameState = {
  // The name the repository lists the mod under. Undefined while the listing
  // is on its way, when the host had none, and for a mod it does not list.
  name: string | undefined;
  isLoading: boolean;
};

// Keyed by language the way the website keys its own read of the catalog: the
// host serves the listing in the app's language, and a change of it is a new
// listing.
const namesKey = (language: string) => ['repositoryModNames', language];

// The names alone, so the session does not hold the listing's other fields for
// them.
function namesOfListing(
  mods: RepositoryModsListing | null
): RepositoryModNames {
  return (
    mods &&
    Object.fromEntries(
      Object.entries(mods).map(([modId, mod]) => [
        modId,
        mod.repository.metadata.name,
      ])
    )
  );
}

/**
 * Hands the names cache a listing a screen read from the host, so a mod link
 * on that screen is named from it rather than by a read of its own.
 */
export function useCacheRepositoryModNames() {
  const { i18n } = useTranslation();
  const { mutate } = useSWRConfig();
  // The language is read when the listing is handed over, not closed over, so
  // the callback holds still and a screen keying its own read on it does not
  // read again on a language change.
  return useCallback(
    (mods: RepositoryModsListing) => {
      void mutate(namesKey(i18n.language), namesOfListing(mods), {
        revalidate: false,
      });
    },
    [i18n, mutate]
  );
}

/**
 * The name the mod repository lists a mod under, out of the host's listing:
 * the one a screen handed over, or else one read here on first use and kept
 * for the session. App builds only - the website is the repository's own
 * host, and draws a link to a mod as the page it leads to.
 */
export function useRepositoryModName(modId: string): RepositoryModNameState {
  const { i18n } = useTranslation();
  const { getRepositoryMods } = useGetRepositoryMods();

  // SWR as the cache and the subscription only: the read below is an effect
  // of its own rather than SWR's fetcher, because the hook it posts through
  // abandons its request on unmount, and the mount-unmount-mount of a strict
  // render would leave SWR deduping the second mount's read against the
  // abandoned first.
  const { data, mutate } = useSWR<RepositoryModNames>(
    namesKey(i18n.language),
    null
  );

  useEffect(() => {
    if (data !== undefined) {
      return;
    }
    let current = true;
    void (async () => {
      const result = await getRepositoryMods({});
      // A request the unmount abandoned leaves the entry as it was: the next
      // mount asks again.
      if (!current || result.status !== 'reply') {
        return;
      }
      await mutate(namesOfListing(result.data.mods), { revalidate: false });
    })();
    return () => {
      current = false;
    };
  }, [data, getRepositoryMods, mutate]);

  return { name: data?.[modId], isLoading: data === undefined };
}
