"""叙事结构 AI 生成服务

负责智能生成和管理叙事结构（部-卷-幕-章）
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from domain.structure.story_node import StoryNode, NodeType
from infrastructure.persistence.database.story_node_repository import StoryNodeRepository

logger = logging.getLogger(__name__)


class StoryStructureAIService:
    """叙事结构 AI 生成服务

    智能生成叙事结构，而非固定模板：
    - 首次进入时生成第一幕
    - 章节完成后判断是否结束当前幕
    - 自动创建下一幕/卷/部
    """

    def __init__(self, repository: StoryNodeRepository):
        self.repository = repository

    async def initialize_first_act(self, novel_id: str) -> Dict[str, Any]:
        """初始化第一幕

        首次进入工作台时调用，AI 生成第一幕的结构和大纲

        Args:
            novel_id: 小说 ID

        Returns:
            生成结果，包含创建的节点信息
        """
        logger.info(f"Initializing first act for novel: {novel_id}")

        # 检查是否已有结构（排除章节节点，只检查幕/卷/部）
        existing = self.repository.get_tree(novel_id)
        structure_nodes = [n for n in existing.nodes if n.node_type in [NodeType.PART, NodeType.VOLUME, NodeType.ACT]]
        if structure_nodes:
            logger.info(f"Structure already exists for novel {novel_id}, skipping initialization")
            return {
                "success": False,
                "message": "叙事结构已存在",
                "nodes_created": 0
            }

        # TODO: 调用 AI 生成第一幕的标题和描述
        # 暂时使用默认值
        act_title = "第一幕：开端"
        act_description = "故事的开始，引入主要人物和冲突"

        # 创建第一幕节点
        act_node = StoryNode(
            id=f"act-{novel_id}-1",
            novel_id=novel_id,
            node_type=NodeType.ACT,
            number=1,
            title=act_title,
            description=act_description,
            parent_id=None,
            order_index=1,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        self.repository.save(act_node)

        logger.info(f"Created first act: {act_node.id}")

        return {
            "success": True,
            "message": "第一幕已创建",
            "nodes_created": 1,
            "act_id": act_node.id,
            "act_title": act_title
        }

    async def check_act_completion(
        self,
        novel_id: str,
        chapter_number: int
    ) -> Dict[str, Any]:
        """检查幕是否完成

        章节生成完成后调用，判断当前幕是否应该结束

        Args:
            novel_id: 小说 ID
            chapter_number: 刚完成的章节号

        Returns:
            检查结果，包含是否需要创建新幕
        """
        logger.info(f"Checking act completion for novel {novel_id}, chapter {chapter_number}")

        # 获取当前章节所属的幕
        tree = self.repository.get_tree(novel_id)
        current_act = self._find_act_for_chapter(tree, chapter_number)

        if not current_act:
            logger.warning(f"No act found for chapter {chapter_number}")
            return {
                "act_completed": False,
                "should_create_next": False
            }

        # TODO: 调用 AI 判断是否应该结束当前幕
        # 暂时使用简单规则：每 10 章一幕
        chapters_in_act = self._count_chapters_in_act(current_act)
        should_end = chapters_in_act >= 10

        logger.info(f"Act {current_act.id} has {chapters_in_act} chapters, should_end={should_end}")

        return {
            "act_completed": should_end,
            "should_create_next": should_end,
            "current_act_id": current_act.id,
            "chapters_in_act": chapters_in_act
        }

    async def create_next_act(
        self,
        novel_id: str,
        previous_act_id: str
    ) -> Dict[str, Any]:
        """创建下一幕

        当前幕完成后自动调用

        Args:
            novel_id: 小说 ID
            previous_act_id: 上一幕的 ID

        Returns:
            创建结果
        """
        logger.info(f"Creating next act for novel {novel_id} after {previous_act_id}")

        # 获取上一幕信息
        previous_act = self.repository.get_by_id(previous_act_id)
        if not previous_act:
            raise ValueError(f"Previous act not found: {previous_act_id}")

        # 计算新幕的编号
        next_number = previous_act.number + 1

        # TODO: 调用 AI 生成下一幕的标题和描述
        act_title = f"第{next_number}幕"
        act_description = f"第{next_number}幕的内容"

        # 创建新幕节点
        act_node = StoryNode(
            id=f"act-{novel_id}-{next_number}",
            novel_id=novel_id,
            node_type=NodeType.ACT,
            number=next_number,
            title=act_title,
            description=act_description,
            parent_id=previous_act.parent_id,  # 继承父节点（卷）
            order_index=previous_act.order_index + 1,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        self.repository.save(act_node)

        logger.info(f"Created next act: {act_node.id}")

        return {
            "success": True,
            "message": f"第{next_number}幕已创建",
            "act_id": act_node.id,
            "act_title": act_title,
            "act_number": next_number
        }

    def _find_act_for_chapter(
        self,
        tree: list[StoryNode],
        chapter_number: int
    ) -> Optional[StoryNode]:
        """查找章节所属的幕"""
        for node in tree:
            if node.node_type == NodeType.ACT:
                if self._chapter_in_range(node, chapter_number):
                    return node
            if node.children:
                result = self._find_act_for_chapter(node.children, chapter_number)
                if result:
                    return result
        return None

    def _chapter_in_range(self, act: StoryNode, chapter_number: int) -> bool:
        """判断章节是否在幕的范围内"""
        if act.chapter_start and act.chapter_end:
            return act.chapter_start <= chapter_number <= act.chapter_end
        return False

    def _count_chapters_in_act(self, act: StoryNode) -> int:
        """统计幕中的章节数"""
        if not act.children:
            return 0

        count = 0
        for child in act.children:
            if child.node_type == NodeType.CHAPTER:
                count += 1
            elif child.children:
                count += self._count_chapters_in_act(child)

        return count
