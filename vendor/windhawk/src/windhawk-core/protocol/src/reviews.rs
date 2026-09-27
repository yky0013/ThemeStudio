//! DTOs of the review-vote commands, `voteModReview`,
//! `retractModReviewVote` and `getModReviewVotes`. A vote crosses the wire
//! as an object where the profile stores a `[timestamp, reviewId]` pair; the
//! conversion is the domain's. camelCase field names match the TS property
//! names so the client does no mapping.

use serde::{Deserialize, Serialize};

////////////////////////////////////////////////////////////////////////////
// voteModReview

#[derive(Serialize, Deserialize, Debug, Clone)]
#[serde(rename_all = "camelCase")]
pub struct VoteModReviewParams {
    pub mod_id: String,
    /// The review's server id; the server's ids start at 1.
    pub review_id: i64,
}

////////////////////////////////////////////////////////////////////////////
// retractModReviewVote

#[derive(Serialize, Deserialize, Debug, Clone)]
#[serde(rename_all = "camelCase")]
pub struct RetractModReviewVoteParams {
    pub mod_id: String,
    /// The id of the review whose vote is taken back.
    pub review_id: i64,
}

////////////////////////////////////////////////////////////////////////////
// getModReviewVotes

#[derive(Serialize, Deserialize, Debug, Clone)]
#[serde(rename_all = "camelCase")]
pub struct GetModReviewVotesParams {
    pub mod_id: String,
}

////////////////////////////////////////////////////////////////////////////
// shared result

/// One recorded upvote: the review's id and when the vote was cast, in unix
/// seconds.
#[derive(Serialize, Deserialize, Debug, Clone, Copy, PartialEq, Eq)]
#[serde(rename_all = "camelCase")]
pub struct ReviewVoteDto {
    pub review_id: i64,
    pub timestamp: i64,
}

/// Result of all three commands: every vote recorded for the mod, in the order
/// the profile holds them (the order they were cast).
#[derive(Serialize, Deserialize, Debug, Clone, PartialEq, Eq, Default)]
#[serde(rename_all = "camelCase")]
pub struct ReviewVotesResult {
    pub votes: Vec<ReviewVoteDto>,
}
