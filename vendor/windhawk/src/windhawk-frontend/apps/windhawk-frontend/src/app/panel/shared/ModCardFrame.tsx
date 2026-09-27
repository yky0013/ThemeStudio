// Extracted from ModCard.tsx by Theme Studio: the original Windhawk Card.Meta,
// ribbon, selection and bottom action layout, without online reviews or routing.
// Windhawk copyright and GPL-3.0 terms are retained in the source root LICENSE.
import { Badge, Card, Checkbox } from 'antd';
import styled, { css } from 'styled-components';
import type { ComponentChildren } from 'preact';
import EllipsisText from '../../components/EllipsisText';
import ModSelectBox, { modSelectBoxReach, modSelectBoxRevealed } from './ModSelectBox';

const ModCardRibbon = styled(Badge.Ribbon)<{ $hidden: boolean }>`
  ${({ $hidden }) => $hidden && css`display: none;`}
`;
const ModCardWrapperInner = styled(Card)`
  height: 100%;
  > .ant-card-body { height: 100%; display: flex; flex-direction: column; > .ant-card-meta { flex: 1; } }
`;
const ModCardTitleContainer = styled.div`display: flex;`;
const ModCardTitle = styled(EllipsisText)`flex: 1;`;
const ModCardActionsContainer = styled.div`
  display: flex; align-items: center; margin-top: 20px; text-align: end; gap: 10px;
  > :last-child { margin-inline-start: auto; }
`;
const ModCardWrapper = styled.div`
  > .ant-ribbon-wrapper { height: 100%; }
  ${ModCardTitleContainer} { ${modSelectBoxReach(12)} }
  .ant-card-meta-detail { overflow: visible; min-width: 0; }
  .ant-card-meta-title { overflow: visible; }
  .ant-card-meta-description { overflow: hidden; }
  &:hover ${ModSelectBox}, &[data-selected] ${ModSelectBox}, [data-selection-active] & ${ModSelectBox} { ${modSelectBoxRevealed} }
  @media (hover: none) { ${ModSelectBox} { ${modSelectBoxRevealed} } }
  &[data-selected] ${ModCardWrapperInner} { background-image: linear-gradient(var(--whui-selected-bg), var(--whui-selected-bg)); border-color: var(--whui-primary); }
`;

export default function ModCardFrame({ id, title, description, selected, onSelect, selectLabel, metadata, actions, ribbon }: {
  id: string; title: string; description: string; selected: boolean; onSelect: (checked: boolean) => void; selectLabel: string;
  metadata: ComponentChildren; actions: ComponentChildren; ribbon?: string;
}) {
  return <ModCardWrapper data-testid="mod-card" data-mod-id={id} data-selected={selected ? '' : undefined}>
    <ModCardRibbon text={ribbon} $hidden={!ribbon}><ModCardWrapperInner size="small">
      <Card.Meta title={<><ModCardTitleContainer><ModSelectBox><Checkbox aria-label={selectLabel} checked={selected} onChange={(event) => onSelect(event.target.checked)} /></ModSelectBox><ModCardTitle tooltipPlacement="bottom">{title}</ModCardTitle></ModCardTitleContainer>{metadata}</>} description={description} />
      <ModCardActionsContainer>{actions}</ModCardActionsContainer>
    </ModCardWrapperInner></ModCardRibbon>
  </ModCardWrapper>;
}
