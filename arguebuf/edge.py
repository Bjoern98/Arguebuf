from __future__ import absolute_import, annotations

import typing as t

import graphviz as gv
import networkx as nx
import pendulum
from arg_services.graph.v1 import graph_pb2

from arguebuf.data import Metadata

from . import dt, utils
from .node import Node


class Edge:
    """Edge in AIF format."""

    __slots__ = (
        "_id",
        "_source",
        "_target",
        "created",
        "updated",
        "metadata",
    )

    _id: str
    _source: Node
    _target: Node
    created: pendulum.DateTime
    updated: pendulum.DateTime
    metadata: Metadata

    def __init__(
        self,
        id: str,
        source: Node,
        target: Node,
        created: t.Optional[pendulum.DateTime] = None,
        updated: t.Optional[pendulum.DateTime] = None,
        metadata: t.Optional[Metadata] = None,
    ):
        self._id = id
        self._source = source
        self._target = target
        self.created = created or pendulum.now()
        self.updated = updated or pendulum.now()
        self.metadata = metadata or {}

        self.__post_init__()

    def __post_init__(self):
        pass

    def __repr__(self):
        return utils.class_repr(
            self,
            [str(self._id), f"{self._source.__repr__()}->{self._target.__repr__()}"],
        )

    @property
    def id(self) -> str:
        return self._id

    @property
    def source(self) -> Node:
        return self._source

    @property
    def target(self) -> Node:
        return self._target

    @classmethod
    def from_ova(
        cls,
        obj: t.Mapping[str, t.Any],
        nodes: t.Mapping[str, Node] = None,
    ) -> Edge:
        if not nodes:
            nodes = {}

        source_id = str(obj["from"]["id"])
        target_id = str(obj["to"]["id"])

        return cls(
            id=utils.unique_id(),
            source=nodes[source_id],
            target=nodes[target_id],
            created=dt.from_ova(obj.get("date")),
            updated=dt.from_ova(obj.get("date")),
        )

    @classmethod
    def from_aif(
        cls,
        obj: t.Any,
        nodes: t.Mapping[str, Node],
    ) -> Edge:
        start_id = obj.get("fromID")
        end_id = obj.get("toID")

        return cls(
            id=obj["edgeID"],
            source=nodes[start_id],
            target=nodes[end_id],
        )

    def to_aif(self) -> t.Dict[str, t.Any]:
        return {
            "edgeID": str(self.id),
            "fromID": str(self.source.id),
            "toID": str(self.target.id),
            "formEdgeID": None,
        }

    @classmethod
    def from_protobuf(
        cls,
        id: str,
        obj: graph_pb2.Edge,
        nodes: t.Mapping[str, Node],
    ) -> Edge:
        return cls(
            id,
            nodes[obj.source],
            nodes[obj.target],
            dt.from_protobuf(obj.created),
            dt.from_protobuf(obj.updated),
            dict(obj.metadata.items()),
        )

    def to_protobuf(self) -> graph_pb2.Edge:
        obj = graph_pb2.Edge(
            source=self._source.id,
            target=self._target.id,
        )
        obj.metadata.update(self.metadata)

        if created := self.created:
            obj.created.FromDatetime(created)

        if updated := self.updated:
            obj.updated.FromDatetime(updated)

        return obj

    def to_nx(self, g: nx.DiGraph) -> None:
        g.add_edge(self.source.id, self.target.id)

    def to_gv(self, g: gv.Digraph) -> None:
        g.edge(
            self.source._id,
            self.target._id,
        )