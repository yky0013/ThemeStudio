//! `services::reviews`: the review-vote commands, `voteModReview`,
//! `retractModReviewVote` and `getModReviewVotes`. A vote is the one durable
//! state of a mod's reviews kept on the machine: a `[timestamp, reviewId]`
//! pair in the user profile, delivered to the update server by the app's next
//! update check. No command here requires the mod to be installed - a vote
//! cast from the online browser is on a mod that may not be - and all go
//! through `services::profile`, the profile's only writer.

use serde_json::Value;
use windhawk_core_domain::{ModId, Profile};
use windhawk_core_protocol::{
    GetModReviewVotesParams, RetractModReviewVoteParams, ReviewVoteDto, ReviewVotesResult,
    VoteModReviewParams,
};

use crate::dispatch::{check_storage_id, decode_params};
use crate::error::CoreError;
use crate::services::profile::{read_modify_write, read_profile};
use crate::services::wire::to_value_result;
use crate::session::SessionInner;

/// A `local@` mod is nobody's copy of a repository mod: it has no reviews to
/// vote on, and the profile takes care never to hold an entry for one.
fn check_repository_mod(command: &str, mod_id: &str) -> Result<(), CoreError> {
    check_storage_id(command, "modId", mod_id)?;
    if ModId::str_is_local(mod_id) {
        return Err(CoreError::invalid_request(format!(
            "{command}: a local mod ({mod_id:?}) has no reviews"
        )));
    }
    Ok(())
}

/// The server's review ids start at 1.
fn check_review_id(command: &str, review_id: i64) -> Result<(), CoreError> {
    if review_id < 1 {
        return Err(CoreError::invalid_request(format!(
            "{command}: invalid reviewId {review_id}; a review id is a positive integer"
        )));
    }
    Ok(())
}

fn votes_result(command: &str, profile: &Profile, mod_id: &str) -> Result<Value, CoreError> {
    let votes = profile
        .mod_review_votes(mod_id)
        .into_iter()
        .map(|vote| ReviewVoteDto {
            review_id: vote.review_id,
            timestamp: vote.timestamp,
        })
        .collect();
    to_value_result(command, &ReviewVotesResult { votes })
}

/// `voteModReview`: record an upvote as an own profile write and answer with
/// the mod's whole list of votes. A repeat of an id already recorded writes
/// nothing and answers the same list: a vote is one way, and a second click
/// is not a second vote. The timestamp is the session clock's, in unix
/// seconds.
pub fn vote_mod_review(session: &SessionInner, params: Value) -> Result<Value, CoreError> {
    let params: VoteModReviewParams = decode_params("voteModReview", params)?;
    check_repository_mod("voteModReview", &params.mod_id)?;
    check_review_id("voteModReview", params.review_id)?;
    let now_seconds = session.deps().clock.now_ms() / 1000;
    read_modify_write(session, false, |profile| {
        let written = profile.add_mod_review_vote(&params.mod_id, params.review_id, now_seconds);
        (
            written,
            votes_result("voteModReview", profile, &params.mod_id),
        )
    })?
}

/// `retractModReviewVote`: take a vote back as an own profile write and
/// answer with the mod's list of votes after it. An id that is not recorded
/// writes nothing and answers the list as it is. How long after the click a
/// vote can be taken back is the front-end's rule; the pair is removed
/// whenever this is asked to, and the profile is then as it was before the
/// vote.
pub fn retract_mod_review_vote(session: &SessionInner, params: Value) -> Result<Value, CoreError> {
    let params: RetractModReviewVoteParams = decode_params("retractModReviewVote", params)?;
    check_repository_mod("retractModReviewVote", &params.mod_id)?;
    check_review_id("retractModReviewVote", params.review_id)?;
    read_modify_write(session, false, |profile| {
        let written = profile.retract_mod_review_vote(&params.mod_id, params.review_id);
        (
            written,
            votes_result("retractModReviewVote", profile, &params.mod_id),
        )
    })?
}

/// `getModReviewVotes`: the votes recorded for a mod, `[]` for one the
/// profile has no entry for.
pub fn get_mod_review_votes(session: &SessionInner, params: Value) -> Result<Value, CoreError> {
    let params: GetModReviewVotesParams = decode_params("getModReviewVotes", params)?;
    check_repository_mod("getModReviewVotes", &params.mod_id)?;
    let profile = read_profile(session)?;
    votes_result("getModReviewVotes", &profile, &params.mod_id)
}
